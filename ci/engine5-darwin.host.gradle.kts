// Disposable validation host inside the extracted App build; never a product module or source copy.
plugins {
    alias(libs.plugins.kotlin.multiplatform)
}

check(path == ":engine5DarwinBoundary")
check(providers.gradleProperty("engine5Role").orNull == "app")
check(libs.versions.kotlin.get() == "2.4.0" && libs.versions.ktor.get() == "3.5.1")

kotlin {
    iosSimulatorArm64()
    sourceSets.configureEach {
        kotlin.setSrcDirs(emptyList<String>())
        resources.setSrcDirs(emptyList<String>())
    }
    sourceSets {
        commonMain {
            kotlin.srcDir(rootProject.file("composeApp/src/commonMain/kotlin"))
            kotlin.include("me/manga/kira/sources/runtime/KtorHttpExecutor.kt")
            dependencies {
                implementation(project(":sources:engine"))
                implementation(libs.ktor.client.core)
            }
        }
        commonTest {
            kotlin.srcDir(rootProject.file("composeApp/src/commonTest/kotlin"))
            kotlin.include(
                "me/manga/kira/sources/runtime/SourceHttpTestFixture.kt",
                "me/manga/kira/sources/runtime/SourceHttpLoopback.kt",
                "me/manga/kira/sources/runtime/SourceHttpLoopbackCases.kt",
            )
            dependencies {
                implementation(kotlin("test"))
                implementation(libs.kotlinx.coroutines.test)
                implementation(libs.ktor.network)
                implementation(libs.ktor.client.mock) // Required by the unchanged shared fixture, not the selected engine.
            }
        }
        iosSimulatorArm64Test {
            kotlin.srcDir(rootProject.file("composeApp/src/iosTest/kotlin"))
            kotlin.include("me/manga/kira/sources/runtime/KtorSourceDarwinBoundaryTest.kt")
            dependencies {
                implementation(libs.ktor.client.darwin)
            }
        }
    }
}
