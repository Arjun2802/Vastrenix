package com.vastrenix.app;

import android.annotation.SuppressLint;
import android.app.Activity;
import android.content.Context;
import android.content.Intent;
import android.content.SharedPreferences;
import android.content.pm.PackageManager;
import android.content.pm.ResolveInfo;
import android.graphics.Bitmap;
import android.net.Uri;
import android.os.Build;
import android.os.Bundle;
import android.os.Handler;
import android.os.Looper;
import android.util.Base64;
import android.util.DisplayMetrics;
import android.util.Log;
import android.view.View;
import android.view.Window;
import android.view.WindowInsets;
import android.view.WindowManager;
import android.webkit.ConsoleMessage;
import android.webkit.DownloadListener;
import android.webkit.JavascriptInterface;
import android.webkit.ValueCallback;
import android.webkit.WebChromeClient;
import android.webkit.WebResourceError;
import android.webkit.WebResourceRequest;
import android.webkit.WebSettings;
import android.webkit.WebView;
import android.webkit.WebViewClient;
import android.widget.Toast;

import java.io.File;
import java.io.FileOutputStream;
import java.io.InputStream;
import java.net.HttpURLConnection;
import java.net.URL;
import java.util.List;

public class MainActivity extends Activity {
    private static final String TAG = "VastrenixApp";
    private static final String PREFS_NAME = "VastrenixPrefs";
    private static final String KEY_SERVER_URL = "server_url";

    private WebView webView;
    private ValueCallback<Uri[]> filePathCallback;
    private Uri cameraCaptureUri;
    private final Handler mainHandler = new Handler(Looper.getMainLooper());

    @SuppressLint({"SetJavaScriptEnabled", "NewApi"})
    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);

        // Professional Immersive System Bars (Graphite Theme #0E0E12)
        Window window = getWindow();
        window.getDecorView().setBackgroundColor(0xFF0E0E12);
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.LOLLIPOP) {
            window.addFlags(WindowManager.LayoutParams.FLAG_DRAWS_SYSTEM_BAR_BACKGROUNDS);
            window.setStatusBarColor(0xFF0E0E12);
            window.setNavigationBarColor(0xFF0E0E12);
        }

        webView = new WebView(this);
        webView.setBackgroundColor(0xFF0E0E12);
        webView.setVerticalScrollBarEnabled(false);
        webView.setHorizontalScrollBarEnabled(false);
        webView.setOverScrollMode(View.OVER_SCROLL_NEVER);
        setContentView(webView);

        // Security Hardening: Gate WebView debugging strictly behind debuggable flag
        final boolean isDebuggable = (getApplicationInfo().flags & android.content.pm.ApplicationInfo.FLAG_DEBUGGABLE) != 0;
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.KITKAT) {
            WebView.setWebContentsDebuggingEnabled(isDebuggable);
        }

        WebSettings settings = webView.getSettings();
        settings.setJavaScriptEnabled(true);
        settings.setDomStorageEnabled(true);
        settings.setDatabaseEnabled(true);
        settings.setLoadWithOverviewMode(true);
        settings.setUseWideViewPort(true);
        settings.setSupportZoom(false);
        settings.setBuiltInZoomControls(false);
        settings.setDisplayZoomControls(false);

        // Security Hardening: Disable arbitrary host filesystem access from URLs
        settings.setAllowFileAccess(false);
        settings.setAllowContentAccess(true);
        // Required for local bundled SPA running from file:///android_asset to access demo.json and Firestore Web SDK
        settings.setAllowFileAccessFromFileURLs(true);
        settings.setAllowUniversalAccessFromFileURLs(true);

        // Security Hardening: Strictly block insecure mixed HTTP content
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.LOLLIPOP) {
            settings.setMixedContentMode(WebSettings.MIXED_CONTENT_NEVER_ALLOW);
        }

        // Register Native Android Javascript Bridge
        webView.addJavascriptInterface(new VastrenixNativeBridge(), "VastrenixNative");

        // Native Download Listener for PDF and files
        webView.setDownloadListener(new DownloadListener() {
            @Override
            public void onDownloadStart(String url, String userAgent, String contentDisposition, String mimeType, long contentLength) {
                Log.d(TAG, "Download requested: " + url + " | MIME: " + mimeType);
                String fileName = "invoice_" + System.currentTimeMillis() + ".pdf";
                downloadAndOpenPdf(url, fileName);
            }
        });

        webView.setWebChromeClient(new WebChromeClient() {
            @Override
            public boolean onConsoleMessage(ConsoleMessage cm) {
                // Security Hardening: Suppress JavaScript logs in release builds to prevent leaking state to logcat
                if (isDebuggable) {
                    Log.d(TAG, "[JS] " + cm.message() + " (" + cm.sourceId() + ":" + cm.lineNumber() + ")");
                }
                return true;
            }

            @Override
            public boolean onJsAlert(WebView view, String url, String message, final android.webkit.JsResult result) {
                new android.app.AlertDialog.Builder(MainActivity.this)
                    .setTitle("VASTRENIX")
                    .setMessage(message)
                    .setPositiveButton(android.R.string.ok, (dialog, which) -> result.confirm())
                    .setOnCancelListener(dialog -> result.cancel())
                    .setCancelable(true)
                    .create()
                    .show();
                return true;
            }

            @Override
            public boolean onJsConfirm(WebView view, String url, String message, final android.webkit.JsResult result) {
                new android.app.AlertDialog.Builder(MainActivity.this)
                    .setTitle("VASTRENIX")
                    .setMessage(message)
                    .setPositiveButton(android.R.string.ok, (dialog, which) -> result.confirm())
                    .setNegativeButton(android.R.string.cancel, (dialog, which) -> result.cancel())
                    .setOnCancelListener(dialog -> result.cancel())
                    .setCancelable(true)
                    .create()
                    .show();
                return true;
            }

            @Override
            public boolean onShowFileChooser(WebView webView, ValueCallback<Uri[]> callback, FileChooserParams params) {
                if (filePathCallback != null) {
                    filePathCallback.onReceiveValue(null);
                    filePathCallback = null;
                }
                filePathCallback = callback;

                try {
                    java.util.ArrayList<Intent> extraIntents = new java.util.ArrayList<>();
                    Intent takePictureIntent = new Intent(android.provider.MediaStore.ACTION_IMAGE_CAPTURE);
                    if (takePictureIntent.resolveActivity(getPackageManager()) != null) {
                        try {
                            File photosDir = new File(getCacheDir(), "photos");
                            if (!photosDir.exists()) photosDir.mkdirs();
                            File photoFile = new File(photosDir, "img_" + System.currentTimeMillis() + ".jpg");
                            cameraCaptureUri = VastrenixFileProvider.getUriForFile(MainActivity.this, photoFile);
                            takePictureIntent.putExtra(android.provider.MediaStore.EXTRA_OUTPUT, cameraCaptureUri);
                            takePictureIntent.addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION | Intent.FLAG_GRANT_WRITE_URI_PERMISSION);
                            extraIntents.add(takePictureIntent);
                        } catch (Exception ex) {
                            Log.e(TAG, "Camera file prep error", ex);
                        }
                    }

                    Intent pickIntent = new Intent(Intent.ACTION_GET_CONTENT);
                    pickIntent.addCategory(Intent.CATEGORY_OPENABLE);
                    pickIntent.setType("image/*");

                    Intent chooserIntent = Intent.createChooser(pickIntent, "Select or Take Photo");
                    if (!extraIntents.isEmpty()) {
                        chooserIntent.putExtra(Intent.EXTRA_INITIAL_INTENTS, extraIntents.toArray(new Intent[0]));
                    }

                    startActivityForResult(chooserIntent, 1001);
                    return true;
                } catch (Exception e) {
                    Log.e(TAG, "Chooser setup failed, falling back to basic picker", e);
                    try {
                        Intent fallbackIntent = new Intent(Intent.ACTION_GET_CONTENT);
                        fallbackIntent.addCategory(Intent.CATEGORY_OPENABLE);
                        fallbackIntent.setType("image/*");
                        startActivityForResult(fallbackIntent, 1001);
                        return true;
                    } catch (Exception ex2) {
                        Log.e(TAG, "All file chooser intents failed", ex2);
                        if (filePathCallback != null) {
                            filePathCallback.onReceiveValue(null);
                            filePathCallback = null;
                        }
                        return false;
                    }
                }
            }
        });

        webView.setWebViewClient(new WebViewClient() {
            @Override
            public void onPageStarted(WebView view, String url, Bitmap favicon) {
                super.onPageStarted(view, url, favicon);
                Log.d(TAG, "Page load started: " + url);
            }

            @Override
            public void onPageFinished(WebView view, String url) {
                super.onPageFinished(view, url);
                Log.d(TAG, "Page load complete: " + url);
            }

            @Override
            public void onReceivedError(WebView view, WebResourceRequest request, WebResourceError error) {
                super.onReceivedError(view, request, error);
                if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.M) {
                    Log.e(TAG, "Web error: " + error.getDescription() + " code: " + error.getErrorCode());
                }
            }

            @Override
            public void onReceivedSslError(WebView view, android.webkit.SslErrorHandler handler, android.net.http.SslError error) {
                // Security Hardening: Strictly cancel SSL errors per Play Store CWE-295 compliance
                Log.w(TAG, "SSL Certificate error on: " + (error.getUrl() != null ? error.getUrl() : "unknown") + " code: " + error.getPrimaryError());
                handler.cancel();
            }

            @Override
            public boolean shouldOverrideUrlLoading(WebView view, String url) {
                return handleExternalUrl(view, Uri.parse(url));
            }

            @Override
            public boolean shouldOverrideUrlLoading(WebView view, WebResourceRequest request) {
                return handleExternalUrl(view, request.getUrl());
            }

            private boolean handleExternalUrl(WebView view, Uri uri) {
                if (uri == null) return false;
                String urlStr = uri.toString();
                // Stay inside local app assets context
                if (urlStr.startsWith("file:///android_asset/") || urlStr.startsWith("data:") || urlStr.startsWith("blob:") || urlStr.startsWith("javascript:")) {
                    return false;
                }
                if (urlStr.endsWith(".pdf") || urlStr.contains("/pdf")) {
                    String fileName = "invoice_" + System.currentTimeMillis() + ".pdf";
                    downloadAndOpenPdf(urlStr, fileName);
                    return true;
                }
                try {
                    Intent intent;
                    if (urlStr.startsWith("intent:")) {
                        intent = Intent.parseUri(urlStr, Intent.URI_INTENT_SCHEME);
                    } else if (urlStr.startsWith("mailto:")) {
                        intent = new Intent(Intent.ACTION_SENDTO, uri);
                    } else if (urlStr.startsWith("tel:")) {
                        intent = new Intent(Intent.ACTION_DIAL, uri);
                    } else {
                        intent = new Intent(Intent.ACTION_VIEW, uri);
                    }
                    intent.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK);
                    startActivity(intent);
                } catch (Exception e) {
                    Log.e(TAG, "Cannot launch external URL: " + urlStr, e);
                    try {
                        if (urlStr.contains("wa.me") || urlStr.contains("whatsapp")) {
                            Intent webWa = new Intent(Intent.ACTION_VIEW, Uri.parse(urlStr));
                            webWa.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK);
                            startActivity(webWa);
                        }
                    } catch (Exception ignored) {}
                }
                return true;
            }
        });

        // Load bundled web app
        webView.loadUrl("file:///android_asset/web/index.html");
    }

    @Override
    protected void onActivityResult(int requestCode, int resultCode, Intent data) {
        if (requestCode == 1001) {
            if (filePathCallback != null) {
                Uri[] results = null;
                if (resultCode == Activity.RESULT_OK) {
                    if (data != null && data.getData() != null) {
                        results = new Uri[]{data.getData()};
                    } else if (data != null && data.getClipData() != null) {
                        int count = data.getClipData().getItemCount();
                        results = new Uri[count];
                        for (int i = 0; i < count; i++) {
                            results[i] = data.getClipData().getItemAt(i).getUri();
                        }
                    } else if (cameraCaptureUri != null) {
                        try {
                            String fileName = cameraCaptureUri.getLastPathSegment();
                            File photoFile = new File(new File(getCacheDir(), "photos"), fileName);
                            if (photoFile.exists() && photoFile.length() > 0) {
                                results = new Uri[]{ cameraCaptureUri };
                            }
                        } catch (Exception ex) {
                            Log.e(TAG, "Error resolving camera capture output", ex);
                        }
                    }
                }
                filePathCallback.onReceiveValue(results);
                filePathCallback = null;
            }
            cameraCaptureUri = null;
        } else {
            super.onActivityResult(requestCode, resultCode, data);
        }
    }

    @Override
    public void onBackPressed() {
        if (webView != null) {
            webView.evaluateJavascript(
                "(function() { " +
                "  if (typeof handleAndroidBack === 'function') { return handleAndroidBack(); } " +
                "  return false; " +
                "})();",
                value -> {
                    if ("false".equals(value) || "null".equals(value)) {
                        if (webView.canGoBack()) {
                            webView.goBack();
                        } else {
                            super.onBackPressed();
                        }
                    }
                }
            );
        } else {
            super.onBackPressed();
        }
    }

    @Override
    protected void onPause() {
        super.onPause();
        if (webView != null) {
            webView.onPause();
            webView.evaluateJavascript("if (typeof window.onAppBackground === 'function') { window.onAppBackground(); }", null);
        }
    }

    @Override
    protected void onResume() {
        super.onResume();
        if (webView != null) {
            webView.onResume();
            webView.evaluateJavascript("if (typeof window.onAppResume === 'function') { window.onAppResume(); }", null);
        }
    }

    // =========================================================================
    // Native PDF Download, FileProvider & Intent Handlers
    // =========================================================================
    public void downloadAndOpenPdf(String pdfUrl, String fileName) {
        new Thread(() -> {
            try {
                File dir = new File(getCacheDir(), "invoices");
                if (!dir.exists()) dir.mkdirs();
                File targetFile = new File(dir, fileName);

                if (pdfUrl.startsWith("data:application/pdf;base64,")) {
                    String base64 = pdfUrl.substring("data:application/pdf;base64,".length());
                    byte[] bytes = Base64.decode(base64, Base64.DEFAULT);
                    try (FileOutputStream fos = new FileOutputStream(targetFile)) {
                        fos.write(bytes);
                    }
                } else {
                    URL u = new URL(pdfUrl);
                    HttpURLConnection conn = (HttpURLConnection) u.openConnection();
                    conn.setRequestMethod("GET");
                    conn.setConnectTimeout(10000);
                    conn.setReadTimeout(15000);
                    conn.connect();

                    try (InputStream in = conn.getInputStream(); FileOutputStream out = new FileOutputStream(targetFile)) {
                        byte[] buffer = new byte[4096];
                        int read;
                        while ((read = in.read(buffer)) != -1) {
                            out.write(buffer, 0, read);
                        }
                    }
                }

                mainHandler.post(() -> launchPdfViewer(targetFile));
            } catch (Exception e) {
                Log.e(TAG, "Failed to download PDF: " + e.getMessage(), e);
                mainHandler.post(() -> Toast.makeText(this, "Unable to load PDF: " + e.getMessage(), Toast.LENGTH_SHORT).show());
            }
        }).start();
    }

    private void launchPdfViewer(File file) {
        try {
            Uri contentUri = VastrenixFileProvider.getUriForFile(this, file);
            Intent intent = new Intent(Intent.ACTION_VIEW);
            intent.setDataAndType(contentUri, "application/pdf");
            intent.addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION);
            intent.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK);

            List<ResolveInfo> resInfoList = getPackageManager().queryIntentActivities(intent, PackageManager.MATCH_DEFAULT_ONLY);
            for (ResolveInfo resolveInfo : resInfoList) {
                String packageName = resolveInfo.activityInfo.packageName;
                grantUriPermission(packageName, contentUri, Intent.FLAG_GRANT_READ_URI_PERMISSION);
            }

            startActivity(intent);
        } catch (Exception e) {
            Log.e(TAG, "Cannot launch PDF viewer: " + e.getMessage(), e);
            Toast.makeText(this, "No PDF viewer app found. Saved to cache: " + file.getName(), Toast.LENGTH_LONG).show();
        }
    }

    private void launchPdfShare(File file) {
        try {
            Uri contentUri = VastrenixFileProvider.getUriForFile(this, file);
            Intent intent = new Intent(Intent.ACTION_SEND);
            intent.setType("application/pdf");
            intent.putExtra(Intent.EXTRA_STREAM, contentUri);
            intent.addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION);

            Intent chooser = Intent.createChooser(intent, "Share Invoice via");
            chooser.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK);
            chooser.addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION);

            List<ResolveInfo> resInfoList = getPackageManager().queryIntentActivities(chooser, PackageManager.MATCH_DEFAULT_ONLY);
            for (ResolveInfo resolveInfo : resInfoList) {
                String packageName = resolveInfo.activityInfo.packageName;
                grantUriPermission(packageName, contentUri, Intent.FLAG_GRANT_READ_URI_PERMISSION);
            }

            startActivity(chooser);
        } catch (Exception e) {
            Log.e(TAG, "Cannot share PDF: " + e.getMessage(), e);
            Toast.makeText(this, "Sharing failed: " + e.getMessage(), Toast.LENGTH_SHORT).show();
        }
    }

    // =========================================================================
    // JavaScript Interface for Web Client
    // =========================================================================
    public class VastrenixNativeBridge {

        @JavascriptInterface
        public void showToast(String message) {
            mainHandler.post(() -> Toast.makeText(MainActivity.this, message, Toast.LENGTH_SHORT).show());
        }

        @JavascriptInterface
        public String getServerUrl() {
            SharedPreferences prefs = getSharedPreferences(PREFS_NAME, MODE_PRIVATE);
            return prefs.getString(KEY_SERVER_URL, "");
        }

        @JavascriptInterface
        public void setServerUrl(String url) {
            SharedPreferences prefs = getSharedPreferences(PREFS_NAME, MODE_PRIVATE);
            prefs.edit().putString(KEY_SERVER_URL, url).apply();
            Log.d(TAG, "Configured custom Server URL: " + url);
        }

        @JavascriptInterface
        public String fetchNative(String urlString, String method, String headersJson, String body) {
            HttpURLConnection conn = null;
            try {
                URL url = new URL(urlString);
                conn = (HttpURLConnection) url.openConnection();
                conn.setRequestMethod(method != null ? method.toUpperCase() : "GET");
                conn.setConnectTimeout(65000);
                conn.setReadTimeout(65000);
                conn.setDoInput(true);
                conn.setInstanceFollowRedirects(true);

                if (headersJson != null && !headersJson.trim().isEmpty()) {
                    org.json.JSONObject headers = new org.json.JSONObject(headersJson);
                    java.util.Iterator<String> keys = headers.keys();
                    while (keys.hasNext()) {
                        String key = keys.next();
                        conn.setRequestProperty(key, headers.getString(key));
                    }
                }

                if (body != null && !body.isEmpty() && !"GET".equalsIgnoreCase(method)) {
                    conn.setDoOutput(true);
                    byte[] outputBytes = body.getBytes(java.nio.charset.StandardCharsets.UTF_8);
                    conn.setFixedLengthStreamingMode(outputBytes.length);
                    try (java.io.OutputStream os = conn.getOutputStream()) {
                        os.write(outputBytes);
                        os.flush();
                    }
                }

                int status = conn.getResponseCode();
                java.io.InputStream is = (status >= 200 && status < 400) ? conn.getInputStream() : conn.getErrorStream();
                String responseBody = "";
                if (is != null) {
                    java.util.Scanner s = new java.util.Scanner(is, "UTF-8").useDelimiter("\\A");
                    responseBody = s.hasNext() ? s.next() : "";
                }

                org.json.JSONObject res = new org.json.JSONObject();
                res.put("status", status);
                res.put("body", responseBody);
                return res.toString();
            } catch (Exception e) {
                Log.e(TAG, "Native HTTP fetch failed for " + urlString + ": " + e.getMessage(), e);
                org.json.JSONObject res = new org.json.JSONObject();
                try {
                    res.put("status", 0);
                    res.put("error", e.getMessage() != null ? e.getMessage() : e.toString());
                } catch (Exception ignored) {}
                return res.toString();
            } finally {
                if (conn != null) {
                    conn.disconnect();
                }
            }
        }

        @JavascriptInterface
        public void openExternalUrl(String url) {
            mainHandler.post(() -> {
                try {
                    Intent intent = new Intent(Intent.ACTION_VIEW, Uri.parse(url));
                    intent.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK);
                    startActivity(intent);
                } catch (Exception e) {
                    Log.e(TAG, "Cannot open external URL: " + e.getMessage());
                }
            });
        }

        @JavascriptInterface
        public void savePdfFromBase64(String base64Data, String fileName) {
            new Thread(() -> {
                try {
                    File downloadsDir = android.os.Environment.getExternalStoragePublicDirectory(android.os.Environment.DIRECTORY_DOWNLOADS);
                    File savedFile = null;
                    byte[] bytes = Base64.decode(base64Data, Base64.DEFAULT);

                    if (downloadsDir != null && (downloadsDir.exists() || downloadsDir.mkdirs())) {
                        savedFile = new File(downloadsDir, fileName);
                        try (FileOutputStream fos = new FileOutputStream(savedFile)) {
                            fos.write(bytes);
                        }
                    }

                    File cacheDir = new File(getCacheDir(), "invoices");
                    if (!cacheDir.exists()) cacheDir.mkdirs();
                    File viewFile = new File(cacheDir, fileName);
                    try (FileOutputStream fos = new FileOutputStream(viewFile)) {
                        fos.write(bytes);
                    }

                    final String msg = (savedFile != null)
                        ? "Invoice saved to Downloads (" + fileName + ")"
                        : "Invoice saved";

                    mainHandler.post(() -> {
                        Toast.makeText(MainActivity.this, msg, Toast.LENGTH_LONG).show();
                        launchPdfViewer(viewFile);
                    });
                } catch (Exception e) {
                    Log.e(TAG, "Error saving base64 PDF: " + e.getMessage(), e);
                    mainHandler.post(() -> Toast.makeText(MainActivity.this, "Save failed: " + e.getMessage(), Toast.LENGTH_SHORT).show());
                }
            }).start();
        }

        @JavascriptInterface
        public void openPdfFromBase64(String base64Data, String fileName) {
            new Thread(() -> {
                try {
                    File dir = new File(getCacheDir(), "invoices");
                    if (!dir.exists()) dir.mkdirs();
                    File file = new File(dir, fileName);
                    byte[] bytes = Base64.decode(base64Data, Base64.DEFAULT);
                    try (FileOutputStream fos = new FileOutputStream(file)) {
                        fos.write(bytes);
                    }
                    mainHandler.post(() -> launchPdfViewer(file));
                } catch (Exception e) {
                    Log.e(TAG, "Error opening base64 PDF: " + e.getMessage(), e);
                }
            }).start();
        }

        @JavascriptInterface
        public void sharePdfFromBase64(String base64Data, String fileName) {
            new Thread(() -> {
                try {
                    File dir = new File(getCacheDir(), "invoices");
                    if (!dir.exists()) dir.mkdirs();
                    File file = new File(dir, fileName);
                    byte[] bytes = Base64.decode(base64Data, Base64.DEFAULT);
                    try (FileOutputStream fos = new FileOutputStream(file)) {
                        fos.write(bytes);
                    }
                    mainHandler.post(() -> launchPdfShare(file));
                } catch (Exception e) {
                    Log.e(TAG, "Error sharing base64 PDF: " + e.getMessage(), e);
                }
            }).start();
        }

        @JavascriptInterface
        public void sharePdfUrl(String pdfUrl, String fileName) {
            new Thread(() -> {
                try {
                    File dir = new File(getCacheDir(), "invoices");
                    if (!dir.exists()) dir.mkdirs();
                    File file = new File(dir, fileName);

                    if (pdfUrl.startsWith("data:application/pdf;base64,")) {
                        String base64 = pdfUrl.substring("data:application/pdf;base64,".length());
                        byte[] bytes = Base64.decode(base64, Base64.DEFAULT);
                        try (FileOutputStream fos = new FileOutputStream(file)) {
                            fos.write(bytes);
                        }
                    } else {
                        URL u = new URL(pdfUrl);
                        HttpURLConnection conn = (HttpURLConnection) u.openConnection();
                        conn.setRequestMethod("GET");
                        conn.setConnectTimeout(10000);
                        conn.setReadTimeout(15000);
                        conn.connect();
                        try (InputStream in = conn.getInputStream(); FileOutputStream out = new FileOutputStream(file)) {
                            byte[] buffer = new byte[4096];
                            int read;
                            while ((read = in.read(buffer)) != -1) {
                                out.write(buffer, 0, read);
                            }
                        }
                    }
                    mainHandler.post(() -> launchPdfShare(file));
                } catch (Exception e) {
                    Log.e(TAG, "Error sharing PDF URL: " + e.getMessage(), e);
                    mainHandler.post(() -> Toast.makeText(MainActivity.this, "Unable to share PDF: " + e.getMessage(), Toast.LENGTH_SHORT).show());
                }
            }).start();
        }

        @JavascriptInterface
        public void openPdfUrl(String url, String fileName) {
            downloadAndOpenPdf(url, fileName);
        }

        @JavascriptInterface
        public String getDeviceInfo() {
            DisplayMetrics metrics = getResources().getDisplayMetrics();
            float dpWidth = metrics.widthPixels / metrics.density;
            float dpHeight = metrics.heightPixels / metrics.density;
            return "{" +
                "\"sdkInt\":" + Build.VERSION.SDK_INT + "," +
                "\"model\":\"" + Build.MODEL + "\"," +
                "\"manufacturer\":\"" + Build.MANUFACTURER + "\"," +
                "\"density\":" + metrics.density + "," +
                "\"dpWidth\":" + dpWidth + "," +
                "\"dpHeight\":" + dpHeight +
                "}";
        }
    }
}
