import fs2._
import fs2.async.mutable.{Queue, Signal}
import scodec.bits._
import messages2._

// experiment of a protocol version without number display
object door2 extends App {

  implicit val executorStrategy = fs2.Strategy.fromFixedDaemonPool(2)


  val K0 = hex"decafbeddeadbeefcaffeebabe421337".bits
  val K1 = hex"be421337decafbeddeadbeefcaffeeba".bits
  val K2 = hex"caffeebabe421337decafbeddeadbeef".bits




  sealed trait DoorState

  object DoorState {
    case object Idle extends DoorState
    case object WaitForOpen extends DoorState
  }




  val doorState = fs2.async.signalOf[Task, DoorState](DoorState.Idle).unsafeRun()

  // random1 register: session number
  val doorRandom1 = fs2.async.signalOf[Task, Option[BitVector]](None).unsafeRun()

  val doorReceive = fs2.async.unboundedQueue[Task, Msg].unsafeRun()

  val publicReceive = fs2.async.unboundedQueue[Task, Msg].unsafeRun()




  object Door {

    // reset registers and go to idle state
    def idle: Task[Unit] = {
      println("going back to idle, resetting registers")
      for {
        _ <- doorState.set(DoorState.Idle)
        _ <- doorRandom1.set(None)
      } yield ()
    }

    // send session signature challenge and go to wait-for-session-signature state
    def sessionSignatureChallenge: Task[Unit] = {
      for {
        _ <- doorState.set(DoorState.WaitForOpen)
        r1 = HMAC.random
        _ <- doorRandom1.set(Some(r1))
        _ <- publicReceive.offer1(Msg.OpeningChallenge(r1))
      } yield ()
    }

    def abort: Task[Unit] = {
      println("abort")
      idle
    }

    def open: Task[Unit] = {
      println("opening door")
      idle
    }

  }

  object Public {

    def sessionSignature(openingChallenge: BitVector): Task[Unit] = {
      val sig = HMAC.sign(openingChallenge, K0)
      doorReceive.offer1(Msg.Open(sig)).map(_ => ())
    }

  }



  val door: Stream[Task, Unit] = {

    ((doorReceive.dequeue zip doorState.continuous) zip doorRandom1.continuous).evalMap[Task, Task, Unit] {
      case ((msg, state), random1) =>
        println(s"(door) state: $state random1: $random1 received: $msg")

        state match {
          case DoorState.Idle =>
            msg match {
              case Msg.Trigger(0x43) => Door.sessionSignatureChallenge
              case _ => Door.abort
            }

          case DoorState.WaitForOpen =>
            (msg, random1) match {
              case (Msg.Open(sig), Some(r1)) =>
                if (HMAC.check(sig, r1, K0)) Door.open
                else Door.abort

              case _ => Door.abort
            }

        }

    }

  }

  val public = {

    for {
      msg <- publicReceive.dequeue
      _ <- Stream.eval[Task, Any] {
        println(s"(public) msg: $msg")

        msg match {
          case Msg.OpeningChallenge(challenge) => Public.sessionSignature(challenge)
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
  doorReceive.offer1(Msg.Trigger(0x43)).unsafeRun()
  scala.io.StdIn.readLine



  println("refuse session signature msg without prior start")
  doorReceive.offer1(Msg.Open(BitVector.empty)).unsafeRun()
  scala.io.StdIn.readLine


}
