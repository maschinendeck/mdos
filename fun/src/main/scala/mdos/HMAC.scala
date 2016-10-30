package mdos

import java.security.MessageDigest

import scodec.bits.BitVector

object HMAC {

  def random: BitVector = BitVector(scala.util.Random.nextInt())

  def concat(xs: BitVector*): BitVector = {
    xs.toList match {
      case x :: Nil => x
      case y :: ys => y ++ delim ++ concat(ys:_*)
      case Nil => BitVector.empty
    }
  }

  lazy val delim = BitVector("|".getBytes)

  def sha256 = MessageDigest.getInstance("SHA-256")

  def sign(value: BitVector, secret: BitVector): BitVector = {
    BitVector(sha256.digest(concat(secret, value).toByteArray))
  }

  def check(sig: BitVector, value: BitVector, secret: BitVector): Boolean = {
    sig == sign(value, secret)
  }


}
