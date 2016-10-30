package mdos

import codecs._
import messages._
import scodec.bits._

// current protocol version
object door1 extends App {



  // dev keys

  val K0 = hex"decafbeddeadbeefcaffeebabe421337".bits
  val K1 = hex"be421337decafbeddeadbeefcaffeeba".bits
  val K2 = hex"caffeebabe421337decafbeddeadbeef".bits



  // testing

  println(triggerCodec.encode(Msg.Trigger(0x42)).map(_.toBin))
  println(triggerChallengeCodec.encode(Msg.TriggerChallenge(16)).map(_.toBin))
  println(authCodec.encode(Msg.Auth(Mode.NoPresenceChallenge, 20, math.pow(2, 24).toInt)).map(_.toBin))
  println(openingChallengeCodec.encode(Msg.OpeningChallenge(0)).map(_.toBin))
  println(openCodec.encode(Msg.Open(1, math.pow(2, 24).toInt)).map(_.toBin))
  println(acknowledgeCodec.encode(Msg.Acknowledge(math.pow(2, 24).toInt)).map(_.toBin))





  // TODO


}
