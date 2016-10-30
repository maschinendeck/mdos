name := "fun"

version := "1.0"

scalaVersion := "2.11.8"

libraryDependencies ++= List(
  "org.typelevel" %% "cats" % "0.7.2",
  "org.scodec" %% "scodec-core" % "1.10.3",
  "org.scodec" %% "scodec-spire" % "0.4.0",
  "org.scodec" %% "scodec-stream" % "1.0.0",
  "co.fs2" %% "fs2-core" % "0.9.1",
  "co.fs2" %% "fs2-io" % "0.9.1"
)