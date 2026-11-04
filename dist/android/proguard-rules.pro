# VASTRENIX Android ProGuard / R8 Keep Rules

# Keep JavaScript Interface Bridge methods
-keepclassmembers class * {
    @android.webkit.JavascriptInterface <methods>;
}

# Keep MainActivity and custom FileProvider
-keep class com.vastrenix.app.MainActivity { *; }
-keep class com.vastrenix.app.MainActivity$VastrenixNativeBridge { *; }
-keep class com.vastrenix.app.VastrenixFileProvider { *; }

# Keep Android WebKit classes
-keep public class * extends android.webkit.WebChromeClient { *; }
-keep public class * extends android.webkit.WebViewClient { *; }
-keep public class * extends android.webkit.DownloadListener { *; }

# Preserve Line Numbers for Crash Reporting
-keepattributes SourceFile,LineNumberTable
-keepattributes *Annotation*,Signature,InnerClasses,EnclosingMethod
