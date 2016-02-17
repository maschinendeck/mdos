
object codecs extends App {

  import scodec.bits._
  import scodec.codecs._
  import scodec.codecs.literals._

  // types for messages

  sealed trait Msg

  object Msg {

    case class Trigger(protocolVersion: Int) extends Msg

    case class TriggerChallenge(triggerChallenge: Int) extends Msg

    case class Auth(presenceFlag: Byte, nc: Int, hmac: Int) extends Msg

    case class OpeningChallenge(openingChallenge: Int) extends Msg

    case class AcknowledgeChallenge(acknowledgeChallenge: Int, hmac: Int) extends Msg

    case class EnteredKeyNotification(hmac: Int) extends Msg

  }


  // binary codecs for messages

  val triggerCodec = (0x01 ~> byte).xmap[Msg.Trigger](protocolVersion => Msg.Trigger(protocolVersion), _.protocolVersion.toByte)

  val triggerChallengeCodec = (0x02 ~> int16).xmap[Msg.TriggerChallenge](triggerChallenge => Msg.TriggerChallenge(triggerChallenge), _.triggerChallenge)

  val authCodec = (0x03 ~> byte ~ int16 ~ int32).xmap[Msg.Auth]({
    case presenceFlag ~ nc ~ hmac => Msg.Auth(presenceFlag, nc, hmac)
  },
    msg => ((msg.presenceFlag, msg.nc), msg.hmac)
  )

  val openingChallengeCodec = (0x04 ~> int32).xmap[Msg.OpeningChallenge](
    openingChallenge => Msg.OpeningChallenge(openingChallenge), _.openingChallenge
  )

  val acknowledgeChallengeCodec = (0x05 ~> int16 ~ int32).xmap[Msg.AcknowledgeChallenge]({
    case acknowledgeChallenge ~ hmac => Msg.AcknowledgeChallenge(acknowledgeChallenge, hmac)
  }, msg => (msg.acknowledgeChallenge, msg.hmac))

  val enteredKeyNotificationCodec = (0x06 ~> int32).xmap[Msg.EnteredKeyNotification](
    hmac => Msg.EnteredKeyNotification(hmac), _.hmac
  )


  // dev keys

  val K0 = hex"decafbeddeadbeefcaffeebabe421337".bits
  val K1 = hex"be421337decafbeddeadbeefcaffeeba".bits
  val K2 = hex"caffeebabe421337decafbeddeadbeef".bits



  // testing

  println(triggerCodec.encode(Msg.Trigger(1)).map(_.toBin))
  println(triggerChallengeCodec.encode(Msg.TriggerChallenge(16)).map(_.toBin))
  println(authCodec.encode(Msg.Auth('0', 20, math.pow(2, 24).toInt)).map(_.toBin))
  println(openingChallengeCodec.encode(Msg.OpeningChallenge(0)).map(_.toBin))
  println(acknowledgeChallengeCodec.encode(Msg.AcknowledgeChallenge(1, math.pow(2, 24).toInt)).map(_.toBin))
  println(enteredKeyNotificationCodec.encode(Msg.EnteredKeyNotification(math.pow(2, 24).toInt)).map(_.toBin))



}
