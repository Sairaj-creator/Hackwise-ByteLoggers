import React from 'react';
import { View, Text, StyleSheet, TouchableOpacity, ScrollView, Image, Alert } from 'react-native';
import { useRouter } from 'expo-router';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { useAuth } from '@/context/AuthContext';
import { Ionicons } from '@expo/vector-icons';

const C = {
  surface: '#f6f6f6',
  onSurface: '#2d2f2f',
  onSurfaceVariant: '#5a5c5c',
  primary: '#006b1b',
  onPrimary: '#d1ffc8',
  primaryContainer: '#91f78e',
  secondaryContainer: '#ffc791',
  tertiaryContainer: '#c1fd7c',
  onSecondaryContainer: '#6a3c00',
  onTertiaryContainer: '#396100',
  errorContainer: '#f95630',
  errorDim: '#b92902',
  surfaceContainerLow: '#f0f1f1',
  surfaceContainerHigh: '#e1e3e3',
  surfaceContainerLowest: '#ffffff',
  outline: '#767777',
};

const DEFAULT_AVATAR = 'https://lh3.googleusercontent.com/aida-public/AB6AXuAShg27lH1Uy0oyaQyZGREeY0SCgowi__hBVe98LnW7FsxeKgI-ydIPwUBzWWkX_olSRNDi8pNyMVHxGtESg6ltLAEMQnk0EfWFvpkooESQRBT5lfD1Q4O5MEQZBx61bzW0yPOSLLHPKLr-VbQe1pgVHPmQIkF4j_eZXqjSo_O2UQJY3NtTNYEb1ZUzjRYGjZAtAogUPhw5PMNb4fRhjgc3Yt0tn7hnBL4uY6DVvdCZLXtGhUGp4iqX12UYcxTYCGXek4lA4ZeemiGT';

export default function ProfileScreen() {
  const insets = useSafeAreaInsets();
  const router = useRouter();
  const { user, logout } = useAuth();

  const handleLogout = () => {
    Alert.alert('Logout', 'Are you sure you want to log out?', [
      { text: 'Cancel', style: 'cancel' },
      { text: 'Logout', style: 'destructive', onPress: async () => { await logout(); router.replace('/'); } },
    ]);
  };

  return (
    <View style={[styles.container, { paddingTop: insets.top }]}>
      {/* TopAppBar */}
      <View style={styles.appBar}>
        <View style={styles.appBarLeft}>
          <View style={styles.headerAvatarWrap}>
            <Image source={{ uri: DEFAULT_AVATAR }} style={styles.headerAvatar} />
          </View>
        </View>
        <Text style={styles.appBarTitle}>The Culinary Editorial</Text>
        <TouchableOpacity style={styles.iconBtn}>
          <Ionicons name="settings-outline" size={24} color={C.onSurfaceVariant} />
        </TouchableOpacity>
      </View>

      <ScrollView contentContainerStyle={styles.contentWrap}>
        {/* Profile Section */}
        <View style={styles.profileSection}>
          <View style={styles.avatarMainWrap}>
            <View style={styles.avatarMainBox}>
              <Image source={{ uri: DEFAULT_AVATAR }} style={styles.avatarMain} />
            </View>
            <View style={styles.editBadge}>
              <Ionicons name="pencil" size={12} color={C.onPrimary} />
            </View>
          </View>
          
          <View style={styles.nameWrap}>
            <Text style={styles.userName}>{user?.name || 'Chef Gastronomy'}</Text>
            <View style={styles.chefIdBadge}>
              <Text style={styles.chefIdText}>Chef ID: #8829-AI</Text>
            </View>
          </View>
        </View>

        {/* Description Area */}
        <View style={styles.descSection}>
          <View style={styles.descHeader}>
            <Ionicons name="document-text" size={20} color={C.secondaryContainer} />
            <Text style={styles.descHeaderTitle}>Description</Text>
          </View>
          <Text style={styles.descText}>
            Passionate about farm-to-table AI-assisted gastronomy. Currently exploring plant-based Italian fusions and optimizing kitchen efficiency through smart pantry tracking.
          </Text>
        </View>

        {/* Actions Bento Grid */}
        <View style={styles.actionsGrid}>
          {/* Action 1 */}
          <TouchableOpacity style={styles.actionBtn} activeOpacity={0.7}>
            <View style={styles.actionLeft}>
              <View style={[styles.actionIconBox, { backgroundColor: C.tertiaryContainer }]}>
                <Ionicons name="time" size={20} color={C.onTertiaryContainer} />
              </View>
              <View>
                <Text style={styles.actionTitle}>Version Feedback</Text>
                <Text style={styles.actionSubtitle}>Check for updates & release notes</Text>
              </View>
            </View>
            <Ionicons name="chevron-forward" size={20} color={C.onSurfaceVariant} />
          </TouchableOpacity>

          {/* Action 2 */}
          <TouchableOpacity style={styles.actionBtn} activeOpacity={0.7}>
            <View style={styles.actionLeft}>
              <View style={[styles.actionIconBox, { backgroundColor: C.secondaryContainer }]}>
                <Ionicons name="chatbubble" size={20} color={C.onSecondaryContainer} />
              </View>
              <View>
                <Text style={styles.actionTitle}>Feedback</Text>
                <Text style={styles.actionSubtitle}>Report bugs or suggest recipes</Text>
              </View>
            </View>
            <Ionicons name="chevron-forward" size={20} color={C.onSurfaceVariant} />
          </TouchableOpacity>

          {/* Action Logout */}
          <TouchableOpacity style={[styles.actionBtn, styles.actionLogout]} onPress={handleLogout} activeOpacity={0.7}>
            <View style={styles.actionLeft}>
              <View style={[styles.actionIconBox, { backgroundColor: C.errorContainer }]}>
                <Ionicons name="log-out" size={20} color="#fff" />
              </View>
              <View>
                <Text style={[styles.actionTitle, { color: C.errorDim }]}>Logout</Text>
                <Text style={styles.actionSubtitle}>Sign out of your editorial account</Text>
              </View>
            </View>
          </TouchableOpacity>
        </View>

        {/* App Meta */}
        <View style={styles.appMeta}>
          <Text style={styles.metaText}>VERDANT AI KITCHEN SYSTEM V2.4.0</Text>
        </View>

      </ScrollView>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: C.surface },
  appBar: {
    flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center',
    paddingHorizontal: 24, paddingVertical: 16, backgroundColor: C.surface,
  },
  appBarLeft: { flexDirection: 'row', alignItems: 'center' },
  headerAvatarWrap: {
    width: 40, height: 40, borderRadius: 20, overflow: 'hidden',
    backgroundColor: C.surfaceContainerHigh, borderWidth: 2, borderColor: 'rgba(0,107,27,0.1)'
  },
  headerAvatar: { width: '100%', height: '100%' },
  appBarTitle: { fontSize: 20, fontWeight: 'bold', fontStyle: 'italic', color: C.primary, letterSpacing: -0.5 },
  iconBtn: { padding: 4 },

  contentWrap: { paddingHorizontal: 24, paddingTop: 32, paddingBottom: 100 },

  profileSection: { alignItems: 'center', marginBottom: 40 },
  avatarMainWrap: { position: 'relative' },
  avatarMainBox: {
    width: 128, height: 128, borderRadius: 32, overflow: 'hidden',
    backgroundColor: C.surfaceContainerLow, shadowColor: '#000', shadowOpacity: 0.05, shadowRadius: 10, elevation: 2
  },
  avatarMain: { width: '100%', height: '100%' },
  editBadge: {
    position: 'absolute', bottom: -8, right: -8, backgroundColor: C.primary,
    padding: 8, borderRadius: 16, shadowColor: '#000', shadowOpacity: 0.1, shadowRadius: 5, elevation: 3
  },
  nameWrap: { alignItems: 'center', marginTop: 16 },
  userName: { fontSize: 28, fontWeight: '900', color: C.onSurface, letterSpacing: -0.5 },
  chefIdBadge: {
    backgroundColor: 'rgba(145,247,142,0.3)', paddingHorizontal: 12, paddingVertical: 4,
    borderRadius: 16, marginTop: 8
  },
  chefIdText: { fontSize: 12, fontWeight: 'bold', color: C.primary },

  descSection: {
    backgroundColor: C.surfaceContainerLowest, borderRadius: 24, padding: 24,
    shadowColor: '#000', shadowOpacity: 0.02, shadowRadius: 10, elevation: 1, marginBottom: 24
  },
  descHeader: { flexDirection: 'row', alignItems: 'center', gap: 8, marginBottom: 12 },
  descHeaderTitle: { fontSize: 16, fontWeight: 'bold', color: C.onSurface },
  descText: { fontSize: 14, color: C.onSurfaceVariant, lineHeight: 22 },

  actionsGrid: { gap: 16 },
  actionBtn: {
    flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between',
    backgroundColor: C.surfaceContainerLow, padding: 24, borderRadius: 24,
  },
  actionLogout: {
    backgroundColor: 'rgba(249,86,48,0.1)', borderWidth: 1, borderColor: 'rgba(249,86,48,0.2)'
  },
  actionLeft: { flexDirection: 'row', alignItems: 'center', gap: 16 },
  actionIconBox: { width: 44, height: 44, borderRadius: 12, alignItems: 'center', justifyContent: 'center' },
  actionTitle: { fontSize: 16, fontWeight: 'bold', color: C.onSurface, marginBottom: 2 },
  actionSubtitle: { fontSize: 12, color: C.onSurfaceVariant },

  appMeta: { alignItems: 'center', paddingVertical: 16, marginTop: 24 },
  metaText: { fontSize: 10, fontWeight: 'bold', color: C.outline, letterSpacing: 1 },
});
