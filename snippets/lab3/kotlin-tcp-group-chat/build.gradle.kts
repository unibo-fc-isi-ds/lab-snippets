plugins {
    kotlin("jvm") version "1.9.23"
    application
}

group = "it.unibo"
version = "1.0-SNAPSHOT"

repositories {
    mavenCentral()
}

dependencies {
    val ktorVersion = "3.0.1"
    implementation("io.ktor:ktor-server-core:$ktorVersion")
    implementation("io.ktor:ktor-server-netty:$ktorVersion")
    implementation("io.ktor:ktor-network:$ktorVersion")
    testImplementation(kotlin("test"))
}

application {
    mainClass.set("it.unibo.MainKt")
}

tasks.named<JavaExec>("run") {
    standardInput = System.`in`
}

tasks.test {
    useJUnitPlatform()
}
kotlin {
    jvmToolchain(17)
}
