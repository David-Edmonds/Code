package com.recipekeeper.app;

import android.app.Activity;
import android.content.ClipData;
import android.content.ClipboardManager;
import android.content.Intent;
import android.graphics.Color;
import android.net.Uri;
import android.os.Bundle;
import android.util.AtomicFile;
import android.webkit.JavascriptInterface;
import android.webkit.ValueCallback;
import android.webkit.WebChromeClient;
import android.webkit.WebResourceRequest;
import android.webkit.WebResourceResponse;
import android.webkit.WebView;
import android.webkit.WebViewClient;
import android.view.View;
import android.view.WindowInsets;
import android.view.WindowManager;
import android.widget.FrameLayout;
import android.widget.Toast;
import java.io.ByteArrayInputStream;
import java.io.File;
import java.io.FileOutputStream;
import java.io.InputStream;
import java.io.OutputStream;
import java.nio.charset.StandardCharsets;
import java.util.HashMap;
import java.util.Map;

/** Offline app shell. All executable content is bundled, never fetched remotely. */
public class MainActivity extends Activity {
    private static final String HOST = "appassets.androidplatform.net";
    private static final int PICK_FILE = 42, SAVE_FILE = 43;
    private WebView web;
    private AtomicFile store;
    private ValueCallback<Uri[]> fileCallback;
    private String pendingExport;

    @Override public void onCreate(Bundle bundle) {
        super.onCreate(bundle);
        store = new AtomicFile(new File(getFilesDir(), "recipes-v1.json"));
        FrameLayout root = new FrameLayout(this);
        root.setBackgroundColor(Color.rgb(247,246,240));
        web = new WebView(this);
        web.setBackgroundColor(Color.rgb(247,246,240));
        root.addView(web, new FrameLayout.LayoutParams(-1,-1));
        setContentView(root);
        getWindow().getDecorView().setSystemUiVisibility(View.SYSTEM_UI_FLAG_LIGHT_STATUS_BAR | View.SYSTEM_UI_FLAG_LIGHT_NAVIGATION_BAR);
        root.setOnApplyWindowInsetsListener((v, insets) -> {
            if (android.os.Build.VERSION.SDK_INT >= 30) {
                android.graphics.Insets i = insets.getInsets(WindowInsets.Type.systemBars() | WindowInsets.Type.ime());
                v.setPadding(i.left,i.top,i.right,i.bottom);
                return WindowInsets.CONSUMED;
            }
            v.setPadding(insets.getSystemWindowInsetLeft(),insets.getSystemWindowInsetTop(),insets.getSystemWindowInsetRight(),insets.getSystemWindowInsetBottom());
            return insets.consumeSystemWindowInsets();
        });
        root.requestApplyInsets();
        web.getSettings().setJavaScriptEnabled(true);
        web.getSettings().setDomStorageEnabled(true);
        web.getSettings().setAllowFileAccess(false);
        web.getSettings().setAllowContentAccess(true); // Only explicitly selected SAF document URIs.
        web.getSettings().setBlockNetworkLoads(true);
        web.getSettings().setMixedContentMode(android.webkit.WebSettings.MIXED_CONTENT_NEVER_ALLOW);
        web.getSettings().setSupportMultipleWindows(false);
        WebView.setWebContentsDebuggingEnabled(false);
        web.addJavascriptInterface(new LocalBridge(), "AndroidBridge");
        web.setWebViewClient(new WebViewClient() {
            @Override public boolean shouldOverrideUrlLoading(WebView v, WebResourceRequest r) { return !isLocal(r.getUrl()); }
            @Override public WebResourceResponse shouldInterceptRequest(WebView v, WebResourceRequest r) {
                Uri uri=r.getUrl();
                if(!isLocal(uri)||!"GET".equals(r.getMethod())) return denied();
                String path=uri.getPath();
                if(path==null||!path.startsWith("/assets/")||path.contains("..")||path.contains("\\")) return denied();
                path=path.substring(8);
                if(path.isEmpty()) path="index.html";
                try {
                    InputStream input=getAssets().open(path);
                    String mime=path.endsWith(".js")?"application/javascript":path.endsWith(".css")?"text/css":path.endsWith(".svg")?"image/svg+xml":path.endsWith(".json")||path.endsWith(".webmanifest")?"application/json":"text/html";
                    Map<String,String> headers=new HashMap<>();
                    headers.put("Content-Security-Policy", "default-src 'none'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; connect-src 'none'; manifest-src 'self'; base-uri 'none'; form-action 'none'");
                    headers.put("X-Content-Type-Options","nosniff");
                    return new WebResourceResponse(mime,"UTF-8",200,"OK",headers,input);
                } catch(Exception e) {return denied();}
            }
        });
        web.setWebChromeClient(new WebChromeClient() {
            @Override public boolean onShowFileChooser(WebView view, ValueCallback<Uri[]> callback, FileChooserParams params) {
                if(fileCallback!=null) fileCallback.onReceiveValue(null);
                fileCallback=callback;
                Intent intent=new Intent(Intent.ACTION_OPEN_DOCUMENT);
                intent.addCategory(Intent.CATEGORY_OPENABLE);
                intent.setType("*/*");
                String[] accept=params.getAcceptTypes();
                if(accept!=null&&accept.length>0) {
                    boolean image=false;
                    for(String t:accept) if(t.contains("image")) image=true;
                    intent.putExtra(Intent.EXTRA_MIME_TYPES,image?new String[]{"image/jpeg","image/png","image/webp"}:new String[]{"application/json","text/plain","application/octet-stream"});
                }
                try {startActivityForResult(intent,PICK_FILE);} catch(Exception e) {callback.onReceiveValue(null);fileCallback=null;message("No file picker is available.");}
                return true;
            }
        });
        web.loadUrl("https://"+HOST+"/assets/index.html");
    }
    private boolean isLocal(Uri uri) {return "https".equals(uri.getScheme())&&HOST.equals(uri.getHost());}
    private WebResourceResponse denied() {return new WebResourceResponse("text/plain","UTF-8",403,"Blocked",new HashMap<>(),new ByteArrayInputStream(new byte[0]));}
    private void message(String text) {runOnUiThread(()->Toast.makeText(this,text,Toast.LENGTH_LONG).show());}

    public class LocalBridge {
        @JavascriptInterface public synchronized String readData() {
            if(!store.getBaseFile().exists())return "";
            try{return new String(store.readFully(),StandardCharsets.UTF_8);}catch(Exception e){return "{unreadable-data";}
        }
        @JavascriptInterface public synchronized boolean writeData(String json) {
            if(json==null||json.length()>12000000)return false;
            FileOutputStream output=null;
            try {new org.json.JSONObject(json);output=store.startWrite();output.write(json.getBytes(StandardCharsets.UTF_8));store.finishWrite(output);return true;}
            catch(Exception e){if(output!=null)store.failWrite(output);return false;}
        }
        @JavascriptInterface public void keepAwake(boolean keep) {runOnUiThread(()->{if(keep)getWindow().addFlags(WindowManager.LayoutParams.FLAG_KEEP_SCREEN_ON);else getWindow().clearFlags(WindowManager.LayoutParams.FLAG_KEEP_SCREEN_ON);});}
        @JavascriptInterface public void copyText(String text) {runOnUiThread(()->{ClipboardManager manager=(ClipboardManager)getSystemService(CLIPBOARD_SERVICE);manager.setPrimaryClip(ClipData.newPlainText("Our Table shopping list",text));});}
        @JavascriptInterface public void exportFile(String name,String content,String mime) {
            if(content==null||content.length()>12000000){message("That export is too large.");return;}
            runOnUiThread(()->{
                if(pendingExport!=null){message("Finish the current export first.");return;}
                pendingExport=content;
                Intent intent=new Intent(Intent.ACTION_CREATE_DOCUMENT);
                intent.addCategory(Intent.CATEGORY_OPENABLE);
                intent.setType("text/plain".equals(mime)?"text/plain":"application/json");
                intent.putExtra(Intent.EXTRA_TITLE,name.replaceAll("[^a-zA-Z0-9._-]","_"));
                try{startActivityForResult(intent,SAVE_FILE);}catch(Exception e){pendingExport=null;message("No save-file picker is available.");}
            });
        }
    }
    @Override protected void onActivityResult(int request,int result,Intent data) {
        super.onActivityResult(request,result,data);
        if(request==PICK_FILE&&fileCallback!=null){fileCallback.onReceiveValue(result==RESULT_OK&&data!=null&&data.getData()!=null?new Uri[]{data.getData()}:null);fileCallback=null;}
        if(request==SAVE_FILE){String text=pendingExport;pendingExport=null;if(result==RESULT_OK&&data!=null&&data.getData()!=null&&text!=null){try(OutputStream out=getContentResolver().openOutputStream(data.getData(),"wt")){if(out==null)throw new java.io.IOException();out.write(text.getBytes(StandardCharsets.UTF_8));message("Backup saved.");}catch(Exception e){message("Backup could not be saved. Please try again.");}}}
    }
    @SuppressWarnings("deprecation") @Override public void onBackPressed() {web.evaluateJavascript("window.handleAndroidBack ? window.handleAndroidBack() : false",value->{if(!"true".equals(value))finish();});}
    @Override protected void onDestroy() {if(fileCallback!=null)fileCallback.onReceiveValue(null);if(web!=null){web.removeJavascriptInterface("AndroidBridge");web.destroy();}super.onDestroy();}
}
