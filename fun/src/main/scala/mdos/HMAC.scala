package mdos

import java.security.MessageDigest

import scodec.bits.BitVector

object HMAC {

  def random: BitVector = BitVector(scala.util.Random.nextInt())

  val lim = BitVector("|".getBytes)

  def sha256 = MessageDigest.getInstance("SHA-256")

  def sign(value: BitVector, secret: BitVector): BitVector = {
    BitVector(sha256.digest((value ++ lim ++ secret).toByteArray))
  }

  def check(sig: BitVector, value: BitVector, secret: BitVector): Boolean = {
    sig == sign(value, secret)
  }


}
