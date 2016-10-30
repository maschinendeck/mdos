package mdos

import fs2._
import scodec.bits._

// experiment of a protocol version
// - no presence challenge
// - no acknowledge
// - no protocol configuration
// - challenge contains time component, refuse sign requests out of time window, prevent
object door3 extends App {

  implicit val executorStrategy = fs2.Strategy.fromFixedDaemonPool(2)


  val K0 = hex"decafbeddeadbeefcaffeebabe421337".bits
  val K1 = hex"be421337decafbeddeadbeefcaffeeba".bits
  val K2 = hex"caffeebabe421337decafbeddeadbeef".bits



  sealed trait Msg

  object Msg {

    // messages to door
    case class Trigger(protocolVersion: Byte, time: Long) extends Msg
    case class Open(hmac: BitVector) extends Msg

    // messages from door
    case class OpeningChallenge(openingChallenge: BitVector, time: Long) extends Msg

  }


  sealed trait DoorState

  object DoorState {
    case object Idle extends DoorState
    case object WaitForOpen extends DoorState
  }




  val doorState = fs2.async.signalOf[Task, DoorState](DoorState.Idle).unsafeRun()

  // opening challenge register
  // - prevent replay attacks by adding a random number
  // - prevent building a dictionary by adding a time window
  val doorOC = fs2.async.signalOf[Task, Option[(BitVector, Long)]](None).unsafeRun()

  val doorReceive = fs2.async.unboundedQueue[Task, Msg].unsafeRun()

  val publicReceive = fs2.async.unboundedQueue[Task, Msg].unsafeRun()




  object Door {

    def idle: Task[Unit] = {
      for {
        _ <- log("reset registers, go to Idle state")
        _ <- doorState.set(DoorState.Idle)
        _ <- doorOC.set(None)
      } yield ()
    }

    def openingChallenge(time: Long): Task[Unit] = {
      for {
        _ <- log("send opening challenge and go to WaitForOpen state")
        _ <- doorState.set(DoorState.WaitForOpen)
        random = HMAC.random
        _ <- doorOC.set(Some(random, time))
        _ <- publicReceive.offer1(Msg.OpeningChallenge(random, time))
      } yield ()
    }

    def abort: Task[Unit] = {
      log("abort") flatMap (_ => idle)
    }

    def open: Task[Unit] = {
      log("opening door") flatMap (_ => idle)
    }

    def log(msg: String): Task[Unit] = {
      Task(println(s"(door) $msg"))
    }

  }

  object Public {

    def sendOpen(openingChallenge: BitVector, time: Long): Task[Unit] = {
      val sig = HMAC.sign(HMAC.concat(openingChallenge, BitVector(time)), K0)
      doorReceive.offer1(Msg.Open(sig)).map(_ => ())
    }

    def log(msg: String): Task[Unit] = {
      Task(println(s"(public) $msg"))
    }

  }



  val door: Stream[Task, Unit] = {

    ((doorReceive.dequeue zip doorState.continuous) zip doorOC.continuous).evalMap[Task, Task, Unit] {
      case ((msg, state), random1) =>
        println(s"(door) receive msg: $msg state: $state random1: $random1")

        state match {
          case DoorState.Idle =>
            msg match {
              case Msg.Trigger(0x43, time) => Door.openingChallenge(time)
              case _ => Door.abort
            }

          case DoorState.WaitForOpen =>
            (msg, random1) match {
              case (Msg.Open(sig), Some((r1, time))) =>
                if (HMAC.check(sig, HMAC.concat(r1, BitVector(time)), K0)) Door.open
                else Door.abort

              case _ => Door.abort
            }

        }

    }

  }

  val public = {

    for {
      msg <- publicReceive.dequeue
      _ <- Stream.eval(Public.log(s"receive msg: $msg"))
      _ <- Stream.eval[Task, Any] {

        msg match {
          case Msg.OpeningChallenge(challenge, time) =>

            val now = System.currentTimeMillis()
            if (math.abs(time - now) < 3600 * 1000) {
              Public.sendOpen(challenge, time)
            } else {
              Public.log("msg out of time window, ignoring")
            }

          case _ => Task.now(())
        }

      }
    } yield ()

  }


  // start asynchronous processes

  door.run.unsafeRunAsync(_ => ())
  public.run.unsafeRunAsync(_ => ())



  // simulate some messages

  println("initialize")
  doorReceive.offer1(Msg.Trigger(0x43, System.currentTimeMillis())).unsafeRun()
  scala.io.StdIn.readLine



  println("refuse Open without prior start")
  doorReceive.offer1(Msg.Open(BitVector.empty)).unsafeRun()
  scala.io.StdIn.readLine


  println("refuse Msg.OpeningChallenge(challenge, time) out of time range")
  publicReceive.offer1(Msg.OpeningChallenge(BitVector.empty, 0)).unsafeRun()
  scala.io.StdIn.readLine


}
