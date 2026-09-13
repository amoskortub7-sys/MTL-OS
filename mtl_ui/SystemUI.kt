package com.mtl.systemui

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
fun MTLLockscreen() {
    Box(
        modifier = Modifier
            .fillMaxSize()
            .background(MTLTheme.DeepForest)
            .padding(24.dp),
        contentAlignment = Alignment.Center
    ) {
        Column(horizontalAlignment = Alignment.CenterHorizontally) {
            Text(
                text = "Welcome 🤗",
                color = MTLTheme.Sand,
                fontSize = 32.sp,
                fontWeight = FontWeight.SemiBold
            )
            Box(
                modifier = Modifier
                    .padding(top = 28.dp)
                    .height(120.dp)
                    .fillMaxWidth()
                    .background(
                        color = MTLTheme.Forest,
                        shape = RoundedCornerShape(36.dp)
                    )
                    .padding(18.dp),
                contentAlignment = Alignment.Center
            ) {
                Row(horizontalArrangement = Arrangement.SpaceEvenly) {
                    QuickAction(label = "Camera")
                    QuickAction(label = "Flash")
                }
            }
        }
    }
}

@Composable
private fun QuickAction(label: String) {
    Box(
        modifier = Modifier
            .background(Color(0xFF123F2C), RoundedCornerShape(24.dp))
            .padding(horizontal = 18.dp, vertical = 10.dp)
    ) {
        Text(label, color = MTLTheme.Sand, fontSize = 16.sp)
    }
}

@Composable
fun MTLStatusBar() {
    Row(
        modifier = Modifier
            .fillMaxWidth()
            .background(MTLTheme.Forest)
            .padding(horizontal = 18.dp, vertical = 10.dp),
        horizontalArrangement = Arrangement.SpaceBetween,
        verticalAlignment = Alignment.CenterVertically
    ) {
        Text("9:41", color = MTLTheme.Sand, fontSize = 14.sp)
        Text("MTL Flow", color = MTLTheme.Orange, fontSize = 14.sp)
        Text("5G", color = MTLTheme.Sand, fontSize = 14.sp)
    }
}
