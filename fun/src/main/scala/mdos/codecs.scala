package mdos

import messages._
import scodec.codecs._
import scodec.codecs.literals._
import shapeless._

// binary codecs for messages
object codecs {


  val modeCodec = byte.xmap[Mode]({
    case 0x00 => Mode.NoPresenceChallenge
    case 0x01 => Mode.UsePresenceChallenge
  }, {
    case Mode.NoPresenceChallenge => 0x00
    case Mode.UsePresenceChallenge => 0x01
  })

  val triggerCodec = (0x00 ~> byte).xmap[Msg.Trigger](
    protocolVersion => Msg.Trigger(protocolVersion),
    _.protocolVersion.toByte
  )

  val triggerChallengeCodec = (0x01 ~> int16).xmap[Msg.TriggerChallenge](
    triggerChallenge => Msg.TriggerChallenge(triggerChallenge),
    _.triggerChallenge
  )

  val authCodec = (0x02 ~> modeCodec :: int16 :: int32).xmap[Msg.Auth](
    {
      case mode :: nc :: hmac :: HNil => Msg.Auth(mode, nc, hmac)
    },
    msg => msg.mode :: msg.nc :: msg.hmac :: HNil
  )

  val openingChallengeCodec = (0x03 ~> int16).xmap[Msg.OpeningChallenge](
    openingChallenge => Msg.OpeningChallenge(openingChallenge),
    _.openingChallenge
  )

  val openCodec = (0x04 ~> int16 :: int32).xmap[Msg.Open]({
    case acknowledgeChallenge :: hmac :: HNil => Msg.Open(acknowledgeChallenge, hmac)
  }, msg => msg.acknowledgeChallenge :: msg.hmac :: HNil)

  val acknowledgeCodec = (0x05 ~> int32).xmap[Msg.Acknowledge](
    hmac => Msg.Acknowledge(hmac), _.hmac
  )

}
