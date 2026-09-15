package com.mtl.launcher;

import android.app.Activity;
import android.content.Intent;
import android.content.pm.ApplicationInfo;
import android.graphics.Color;
import android.graphics.drawable.GradientDrawable;
import android.os.Bundle;
import android.view.Gravity;
import android.widget.Button;
import android.widget.LinearLayout;
import android.widget.TextView;

import java.text.SimpleDateFormat;
import java.util.ArrayList;
import java.util.Date;
import java.util.List;
import java.util.Locale;

public class MainActivity extends Activity {
    private static final int FOREST = Color.rgb(10, 47, 31);
    private static final int DEEP_FOREST = Color.rgb(8, 26, 18);
    private static final int SAND = Color.rgb(230, 213, 184);
    private static final int ORANGE = Color.rgb(255, 107, 53);

    @Override
    protected void onCreate(Bundle state) {
        super.onCreate(state);
        setContentView(buildHome());
    }

    private LinearLayout buildHome() {
        LinearLayout root = new LinearLayout(this);
        root.setOrientation(LinearLayout.VERTICAL);
        root.setPadding(28, 24, 28, 24);
        root.setBackgroundColor(DEEP_FOREST);

        LinearLayout top = new LinearLayout(this);
        top.setGravity(Gravity.CENTER_VERTICAL);
        TextView time = text(new SimpleDateFormat("HH:mm", Locale.getDefault()).format(new Date()), 42, SAND);
        top.addView(time, new LinearLayout.LayoutParams(0, -2, 1));
        TextView label = text("MTL FLOW", 13, ORANGE);
        label.setGravity(Gravity.CENTER);
        top.addView(label, new LinearLayout.LayoutParams(-2, -2));
        root.addView(top, new LinearLayout.LayoutParams(-1, -2));

        TextView greeting = text("Move through your day", 18, SAND);
        greeting.setPadding(0, 12, 0, 20);
        root.addView(greeting);

        LinearLayout appGrid = new LinearLayout(this);
        appGrid.setOrientation(LinearLayout.VERTICAL);
        List<AppEntry> entries = findLaunchableApps();
        for (int row = 0; row < 2; row++) {
            LinearLayout rowView = new LinearLayout(this);
            rowView.setGravity(Gravity.CENTER);
            for (int column = 0; column < 4; column++) {
                int index = row * 4 + column;
                if (index < entries.size()) {
                    AppEntry entry = entries.get(index);
                    Button tile = action(entry.label, SAND);
                    tile.setOnClickListener(view -> launch(entry.packageName));
                    rowView.addView(tile, new LinearLayout.LayoutParams(0, 92, 1));
                }
            }
            appGrid.addView(rowView, new LinearLayout.LayoutParams(-1, 104));
        }
        root.addView(appGrid, new LinearLayout.LayoutParams(-1, 208));

        TextView space = text("Flow space", 14, Color.rgb(128, 194, 123));
        space.setGravity(Gravity.CENTER);
        root.addView(space, new LinearLayout.LayoutParams(-1, 0, 1));

        LinearLayout dock = new LinearLayout(this);
        dock.setGravity(Gravity.CENTER);
        dock.setPadding(12, 8, 12, 8);
        dock.setBackground(round(FOREST, 42));
        addDockButton(dock, "Phone", "com.google.android.dialer");
        addDockButton(dock, "Messages", "com.google.android.apps.messaging");
        addDockButton(dock, "Camera", "com.android.camera2");
        addDockButton(dock, "Settings", "com.android.settings");
        root.addView(dock, new LinearLayout.LayoutParams(-1, 76));
        return root;
    }

    private List<AppEntry> findLaunchableApps() {
        List<AppEntry> result = new ArrayList<>();
        Intent query = new Intent(Intent.ACTION_MAIN);
        query.addCategory(Intent.CATEGORY_LAUNCHER);
        List<android.content.pm.ResolveInfo> activities = getPackageManager().queryIntentActivities(query, 0);
        for (android.content.pm.ResolveInfo resolve : activities) {
            ApplicationInfo info = resolve.activityInfo.applicationInfo;
            if (!getPackageName().equals(info.packageName)) {
                result.add(new AppEntry(info.loadLabel(getPackageManager()).toString(), info.packageName));
            }
            if (result.size() == 8) break;
        }
        return result;
    }

    private void addDockButton(LinearLayout dock, String label, String packageName) {
        Button button = action(label, SAND);
        button.setOnClickListener(view -> launch(packageName));
        dock.addView(button, new LinearLayout.LayoutParams(0, -1, 1));
    }

    private void launch(String packageName) {
        Intent launch = getPackageManager().getLaunchIntentForPackage(packageName);
        if (launch != null) startActivity(launch);
    }

    private Button action(String label, int color) {
        Button button = new Button(this);
        button.setText(label);
        button.setTextColor(color);
        button.setTextSize(13);
        button.setAllCaps(false);
        button.setBackground(round(Color.rgb(22, 61, 46), 24));
        return button;
    }

    private TextView text(String value, float size, int color) {
        TextView view = new TextView(this);
        view.setText(value);
        view.setTextSize(size);
        view.setTextColor(color);
        return view;
    }

    private GradientDrawable round(int color, int radius) {
        GradientDrawable drawable = new GradientDrawable();
        drawable.setColor(color);
        drawable.setCornerRadius(radius);
        return drawable;
    }

    private record AppEntry(String label, String packageName) {}
}