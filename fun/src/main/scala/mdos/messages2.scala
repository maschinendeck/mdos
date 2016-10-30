package mdos

import scodec.bits.BitVector

object messages2 {

  sealed trait Msg

  object Msg {

    // messages to door
    case class Trigger(protocolVersion: Int) extends Msg
    case class Open(hmac: BitVector) extends Msg

    // messages from door
    case class OpeningChallenge(openingChallenge: BitVector) extends Msg

  }


}
