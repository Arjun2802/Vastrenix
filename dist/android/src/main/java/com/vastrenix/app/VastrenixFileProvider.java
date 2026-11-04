package com.vastrenix.app;

import android.content.ContentProvider;
import android.content.ContentValues;
import android.content.Context;
import android.database.Cursor;
import android.database.MatrixCursor;
import android.net.Uri;
import android.os.ParcelFileDescriptor;
import android.provider.OpenableColumns;
import android.webkit.MimeTypeMap;

import java.io.File;
import java.io.FileNotFoundException;

public class VastrenixFileProvider extends ContentProvider {
    public static final String AUTHORITY = "com.vastrenix.app.fileprovider";

    public static Uri getUriForFile(Context context, File file) {
        return new Uri.Builder()
                .scheme("content")
                .authority(AUTHORITY)
                .path(file.getName())
                .build();
    }

    @Override
    public boolean onCreate() {
        return true;
    }

    @Override
    public ParcelFileDescriptor openFile(Uri uri, String mode) throws FileNotFoundException {
        Context context = getContext();
        if (context == null) {
            throw new FileNotFoundException("Context is null");
        }

        String fileName = uri.getLastPathSegment();
        if (fileName == null || fileName.contains("..")) {
            throw new FileNotFoundException("Invalid file path in URI: " + uri);
        }

        File file = new File(new File(context.getCacheDir(), "photos"), fileName);
        if (!file.getParentFile().exists()) file.getParentFile().mkdirs();

        if (!file.exists()) {
            File invoicesDir = new File(context.getCacheDir(), "invoices");
            File inv = new File(invoicesDir, fileName);
            if (inv.exists()) {
                file = inv;
            } else {
                File altDir = new File(context.getFilesDir(), "invoices");
                File alt = new File(altDir, fileName);
                if (alt.exists()) {
                    file = alt;
                }
            }
        }

        int pfdMode = ParcelFileDescriptor.MODE_READ_ONLY;
        if (mode != null && (mode.contains("w") || mode.contains("rw"))) {
            pfdMode = ParcelFileDescriptor.MODE_READ_WRITE | ParcelFileDescriptor.MODE_CREATE;
        }

        return ParcelFileDescriptor.open(file, pfdMode);
    }

    @Override
    public Cursor query(Uri uri, String[] projection, String selection, String[] selectionArgs, String sortOrder) {
        String fileName = uri.getLastPathSegment();
        if (fileName == null) return null;

        Context context = getContext();
        if (context == null) return null;

        File file = new File(new File(context.getCacheDir(), "photos"), fileName);
        if (!file.exists()) {
            file = new File(new File(context.getCacheDir(), "invoices"), fileName);
            if (!file.exists()) {
                file = new File(new File(context.getFilesDir(), "invoices"), fileName);
            }
        }

        String[] cols = projection != null ? projection : new String[]{
                OpenableColumns.DISPLAY_NAME,
                OpenableColumns.SIZE
        };

        MatrixCursor cursor = new MatrixCursor(cols, 1);
        MatrixCursor.RowBuilder row = cursor.newRow();

        for (String col : cols) {
            if (OpenableColumns.DISPLAY_NAME.equals(col)) {
                row.add(fileName);
            } else if (OpenableColumns.SIZE.equals(col)) {
                row.add(file.exists() ? file.length() : 0);
            } else {
                row.add(null);
            }
        }
        return cursor;
    }

    @Override
    public String getType(Uri uri) {
        String fileName = uri.getLastPathSegment();
        if (fileName != null) {
            int dot = fileName.lastIndexOf('.');
            if (dot >= 0) {
                String ext = fileName.substring(dot + 1).toLowerCase();
                String mime = MimeTypeMap.getSingleton().getMimeTypeFromExtension(ext);
                if (mime != null) return mime;
            }
        }
        return "application/pdf";
    }

    @Override
    public Uri insert(Uri uri, ContentValues values) {
        throw new UnsupportedOperationException("Insert not supported");
    }

    @Override
    public int delete(Uri uri, String selection, String[] selectionArgs) {
        throw new UnsupportedOperationException("Delete not supported");
    }

    @Override
    public int update(Uri uri, ContentValues values, String selection, String[] selectionArgs) {
        throw new UnsupportedOperationException("Update not supported");
    }
}
