package mdos


object messages1 {

  sealed trait Mode

  object Mode {

    case object UsePresenceChallenge extends Mode
    case object NoPresenceChallenge extends Mode

  }

  sealed trait Msg

  object Msg {

    // messages to door
    case class Trigger(protocolVersion: Int) extends Msg
    case class Auth(mode: Mode, nc: Int, hmac: Int) extends Msg
    case class Open(acknowledgeChallenge: Int, hmac: Int) extends Msg

    // messages from door
    case class TriggerChallenge(triggerChallenge: Int) extends Msg
    case class OpeningChallenge(openingChallenge: Int) extends Msg
    case class Acknowledge(hmac: Int) extends Msg

  }


}
