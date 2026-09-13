package com.mtl.launcher

import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.mtl.ui.MTLTheme

@Composable
fun MTLFlowLauncher() {
    Box(
        modifier = Modifier
            .fillMaxSize()
            .background(MTLTheme.DeepForest)
            .padding(18.dp),
        contentAlignment = Alignment.BottomCenter
    ) {
        Column(
            modifier = Modifier.fillMaxSize(),
            verticalArrangement = Arrangement.SpaceBetween,
            horizontalAlignment = Alignment.CenterHorizontally
        ) {
            Row(
                modifier = Modifier
                    .fillMaxWidth()
                    .padding(top = 18.dp),
                horizontalArrangement = Arrangement.SpaceAround
            ) {
                AppBubble("Phone")
                AppBubble("Chat")
                AppBubble("Store")
            }

            Box(
                modifier = Modifier
                    .fillMaxWidth(0.86f)
                    .height(72.dp)
                    .background(MTLTheme.Forest, RoundedCornerShape(36.dp))
                    .padding(horizontal = 20.dp),
                contentAlignment = Alignment.Center
            ) {
                Row(horizontalArrangement = Arrangement.SpaceEvenly) {
                    DockApp("Cam")
                    DockApp("Msg")
                    DockApp("AI")
                }
            }
        }
    }
}

@Composable
private fun AppBubble(label: String) {
    Box(
        modifier = Modifier
            .background(Color(0xFF163D2E), RoundedCornerShape(28.dp))
            .padding(horizontal = 20.dp, vertical = 18.dp)
    ) {
        Text(label, color = MTLTheme.Sand, fontSize = 18.sp, fontWeight = FontWeight.Medium)
    }
}

@Composable
private fun DockApp(label: String) {
    Text(label, color = MTLTheme.Sand, fontSize = 16.sp, fontWeight = FontWeight.Medium)
}
