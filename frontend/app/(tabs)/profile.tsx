import React, { useState, useEffect } from 'react';
import {
  View, Text, StyleSheet, TouchableOpacity, ScrollView,
  Image, Alert, Modal, TextInput, KeyboardAvoidingView,
  Platform, ActivityIndicator,
} from 'react-native';
import { useRouter } from 'expo-router';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { useAuth } from '@/context/AuthContext';
import { Ionicons } from '@expo/vector-icons';
import { api } from '@/services/api';

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

const APP_VERSION = '1.0.0';

const CHANGELOG = [
  {
    version: '1.0.0',
    date: 'April 4, 2025',
    label: 'Initial Launch 🚀',
    labelColor: C.primary,
    labelBg: 'rgba(145,247,142,0.3)',
    changes: [
      'AI recipe generation tailored to your personal taste & dietary preferences',
      'Scan your fridge with camera — auto-detect ingredients using CNN image recognition',
      'Type ingredients manually or drop an image to generate recipes instantly',
      'Smart recipe suggestions based on what you already have at home',
      'Step-by-step cooking mode with timers and instructions',
      'Nutrient breakdown per generated recipe',
      'Save & favorite recipes for later access',
      'In-app feedback system — report bugs or suggest new features',
      'Version update logs so you\'re always in the loop',
    ],
  },
];

const FEEDBACK_TYPES = [
  { id: 'bug', label: '🐛 Bug Report', color: C.errorContainer },
  { id: 'feature', label: '✨ Feature Request', color: C.primary },
  { id: 'recipe', label: '🍽️ Recipe Suggestion', color: C.onSecondaryContainer },
  { id: 'other', label: '💬 Other', color: C.onSurfaceVariant },
];

const DEFAULT_AVATAR = 'https://lh3.googleusercontent.com/aida-public/AB6AXuAShg27lH1Uy0oyaQyZGREeY0SCgowi__hBVe98LnW7FsxeKgI-ydIPwUBzWWkX_olSRNDi8pNyMVHxGtESg6ltLAEMQnk0EfWFvpkooESQRBT5lfD1Q4O5MEQZBx61bzW0yPOSLLHPKLr-VbQe1pgVHPmQIkF4j_eZXqjSo_O2UQJY3NtTNYEb1ZUzjRYGjZAtAogUPhw5PMNb4fRhjgc3Yt0tn7hnBL4uY6DVvdCZLXtGhUGp4iqX12UYcxTYCGXek4lA4ZeemiGT';

export default function ProfileScreen() {
  const insets = useSafeAreaInsets();
  const router = useRouter();
  const { user, logout, updateProfile } = useAuth();

  // Modal states
  const [versionModalVisible, setVersionModalVisible] = useState(false);
  const [feedbackModalVisible, setFeedbackModalVisible] = useState(false);
  const [allFeedbackVisible, setAllFeedbackVisible] = useState(false);

  // Feedback form state
  const [selectedType, setSelectedType] = useState<string | null>(null);
  const [feedbackText, setFeedbackText] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [submitted, setSubmitted] = useState(false);

  // Bio state
  const [isEditingBio, setIsEditingBio] = useState(false);
  const [bioInput, setBioInput] = useState(user?.bio || '');
  const [savingBio, setSavingBio] = useState(false);

  useEffect(() => {
    if (user?.bio) {
      setBioInput(user.bio);
    }
  }, [user?.bio]);

  // All feedback state
  const [allFeedback, setAllFeedback] = useState<any[]>([]);
  const [loadingFeedback, setLoadingFeedback] = useState(false);

  const openAllFeedback = async () => {
    setAllFeedbackVisible(true);
    setLoadingFeedback(true);
    try {
      const data = await api.getFeedback();
      setAllFeedback(data);
    } catch (e: any) {
      Alert.alert('Error', e.message || 'Could not load feedback.');
      setAllFeedbackVisible(false);
    } finally {
      setLoadingFeedback(false);
    }
  };

  const TYPE_META: Record<string, { emoji: string; color: string; bg: string }> = {
    bug:     { emoji: '🐛', color: C.errorDim,           bg: 'rgba(249,86,48,0.12)' },
    feature: { emoji: '✨', color: C.primary,            bg: 'rgba(145,247,142,0.25)' },
    recipe:  { emoji: '🍽️', color: C.onSecondaryContainer, bg: 'rgba(255,199,145,0.3)' },
    other:   { emoji: '💬', color: C.onSurfaceVariant,   bg: C.surfaceContainerHigh },
  };

  const formatDate = (iso: string) => {
    const d = new Date(iso);
    return d.toLocaleDateString('en-IN', { day: 'numeric', month: 'short', year: 'numeric', hour: '2-digit', minute: '2-digit' });
  };

  const handleSaveBio = async () => {
    if (bioInput.trim() === user?.bio) {
      setIsEditingBio(false);
      return;
    }
    setSavingBio(true);
    try {
      if (updateProfile) {
        await updateProfile({ bio: bioInput.trim() });
      }
      setIsEditingBio(false);
    } catch (e: any) {
      Alert.alert('Error', e.message || 'Failed to update bio.');
    } finally {
      setSavingBio(false);
    }
  };

  const handleLogout = () => {
    Alert.alert('Logout', 'Are you sure you want to log out?', [
      { text: 'Cancel', style: 'cancel' },
      { text: 'Logout', style: 'destructive', onPress: async () => { await logout(); router.replace('/'); } },
    ]);
  };

  const handleFeedbackSubmit = async () => {
    if (!selectedType) {
      Alert.alert('Select a type', 'Please choose a feedback category.');
      return;
    }
    if (!feedbackText.trim() || feedbackText.trim().length < 10) {
      Alert.alert('More detail needed', 'Please write at least 10 characters.');
      return;
    }
    setSubmitting(true);
    try {
      await api.submitFeedback(selectedType, feedbackText.trim());
      setSubmitted(true);
    } catch (e: any) {
      Alert.alert('Error', e.message || 'Failed to submit feedback. Please try again.');
    } finally {
      setSubmitting(false);
    }
  };

  const closeFeedbackModal = () => {
    setFeedbackModalVisible(false);
    setSelectedType(null);
    setFeedbackText('');
    setSubmitting(false);
    setSubmitted(false);
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
        <Text style={styles.appBarTitle}>Ingredia</Text>
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
            <View style={{ flexDirection: 'row', alignItems: 'center', gap: 8 }}>
              <Ionicons name="document-text" size={20} color={C.secondaryContainer} />
              <Text style={styles.descHeaderTitle}>Description</Text>
            </View>
            {!isEditingBio ? (
              <TouchableOpacity onPress={() => setIsEditingBio(true)} style={styles.editBioBtn}>
                <Ionicons name="pencil" size={14} color={C.onSurfaceVariant} />
                <Text style={styles.editBioBtnText}>Edit</Text>
              </TouchableOpacity>
            ) : null}
          </View>
          
          {isEditingBio ? (
            <View style={styles.bioEditWrap}>
              <TextInput
                style={styles.bioInput}
                multiline
                numberOfLines={3}
                textAlignVertical="top"
                value={bioInput}
                onChangeText={setBioInput}
                placeholder="Write a little about your culinary journey..."
                placeholderTextColor={C.outline}
                maxLength={300}
                autoFocus
              />
              <View style={styles.bioActions}>
                <TouchableOpacity 
                  disabled={savingBio} 
                  onPress={() => {
                    setBioInput(user?.bio || '');
                    setIsEditingBio(false);
                  }} 
                  style={styles.bioCancelBtn}
                >
                  <Text style={styles.bioCancelText}>Cancel</Text>
                </TouchableOpacity>
                <TouchableOpacity 
                  disabled={savingBio} 
                  onPress={handleSaveBio} 
                  style={styles.bioSaveBtn}
                >
                  {savingBio ? (
                    <ActivityIndicator size="small" color="#fff" />
                  ) : (
                    <Text style={styles.bioSaveText}>Save</Text>
                  )}
                </TouchableOpacity>
              </View>
            </View>
          ) : (
            <Text style={styles.descText}>
              {user?.bio || 'Passionate about farm-to-table AI-assisted gastronomy. Currently exploring plant-based Italian fusions and optimizing kitchen efficiency through smart pantry tracking.'}
            </Text>
          )}
        </View>

        {/* Actions Bento Grid */}
        <View style={styles.actionsGrid}>
          {/* Version Feedback */}
          <TouchableOpacity style={styles.actionBtn} activeOpacity={0.7} onPress={() => setVersionModalVisible(true)}>
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

          {/* Feedback */}
          <TouchableOpacity style={styles.actionBtn} activeOpacity={0.7} onPress={() => setFeedbackModalVisible(true)}>
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

          {/* View All Feedback — Admin only */}
          {user?.is_admin && (
            <TouchableOpacity style={styles.actionBtn} activeOpacity={0.7} onPress={openAllFeedback}>
              <View style={styles.actionLeft}>
                <View style={[styles.actionIconBox, { backgroundColor: 'rgba(145,247,142,0.35)' }]}>
                  <Ionicons name="list" size={20} color={C.primary} />
                </View>
                <View>
                  <Text style={styles.actionTitle}>All Feedback</Text>
                  <Text style={styles.actionSubtitle}>View all submitted feedback</Text>
                </View>
              </View>
              <Ionicons name="chevron-forward" size={20} color={C.onSurfaceVariant} />
            </TouchableOpacity>
          )}

          {/* Logout */}
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
          <Text style={styles.metaText}>HACKWISE BYTELOGGERS · V{APP_VERSION} · INITIAL RELEASE</Text>
        </View>
      </ScrollView>

      {/* ─── ALL FEEDBACK MODAL ─── */}
      <Modal visible={allFeedbackVisible} animationType="slide" transparent onRequestClose={() => setAllFeedbackVisible(false)}>
        <View style={styles.modalOverlay}>
          <View style={styles.modalSheet}>
            <View style={styles.sheetHandle} />
            <View style={styles.modalHeader}>
              <View style={styles.modalHeaderLeft}>
                <View style={[styles.modalIconBox, { backgroundColor: 'rgba(145,247,142,0.35)' }]}>
                  <Ionicons name="list" size={22} color={C.primary} />
                </View>
                <View>
                  <Text style={styles.modalTitle}>All Feedback</Text>
                  <Text style={styles.modalSubtitle}>Submitted by users</Text>
                </View>
              </View>
              <TouchableOpacity onPress={() => setAllFeedbackVisible(false)} style={styles.closeBtn}>
                <Ionicons name="close" size={22} color={C.onSurfaceVariant} />
              </TouchableOpacity>
            </View>

            {loadingFeedback ? (
              <View style={styles.fbLoadingWrap}>
                <ActivityIndicator size="large" color={C.primary} />
                <Text style={styles.fbLoadingText}>Loading feedback...</Text>
              </View>
            ) : allFeedback.length === 0 ? (
              <View style={styles.fbLoadingWrap}>
                <Text style={{ fontSize: 40 }}>📭</Text>
                <Text style={styles.fbEmptyText}>No feedback submitted yet.</Text>
              </View>
            ) : (
              <ScrollView style={{ maxHeight: 520 }} showsVerticalScrollIndicator={false}>
                {allFeedback.map((item, idx) => {
                  const meta = TYPE_META[item.type] || TYPE_META.other;
                  return (
                    <View key={item.id || idx} style={styles.fbCard}>
                      <View style={styles.fbCardTop}>
                        <View style={[styles.fbTypeBadge, { backgroundColor: meta.bg }]}>
                          <Text style={[styles.fbTypeBadgeText, { color: meta.color }]}>
                            {meta.emoji} {item.type}
                          </Text>
                        </View>
                        <Text style={styles.fbTime}>{formatDate(item.submitted_at)}</Text>
                      </View>
                      <Text style={styles.fbUserName}>{item.user_name}</Text>
                      <Text style={styles.fbMessage}>{item.message}</Text>
                    </View>
                  );
                })}
                <View style={{ height: 24 }} />
              </ScrollView>
            )}
          </View>
        </View>
      </Modal>

      {/* ─── VERSION FEEDBACK MODAL ─── */}
      <Modal visible={versionModalVisible} animationType="slide" transparent onRequestClose={() => setVersionModalVisible(false)}>
        <View style={styles.modalOverlay}>
          <View style={styles.modalSheet}>
            {/* Handle */}
            <View style={styles.sheetHandle} />

            {/* Header */}
            <View style={styles.modalHeader}>
              <View style={styles.modalHeaderLeft}>
                <View style={[styles.modalIconBox, { backgroundColor: C.tertiaryContainer }]}>
                  <Ionicons name="rocket" size={22} color={C.onTertiaryContainer} />
                </View>
                <View>
                  <Text style={styles.modalTitle}>Release Notes</Text>
                  <Text style={styles.modalSubtitle}>Current version: v{APP_VERSION}</Text>
                </View>
              </View>
              <TouchableOpacity onPress={() => setVersionModalVisible(false)} style={styles.closeBtn}>
                <Ionicons name="close" size={22} color={C.onSurfaceVariant} />
              </TouchableOpacity>
            </View>

            {/* Up to date badge */}
            <View style={styles.upToDateBadge}>
              <Ionicons name="checkmark-circle" size={16} color={C.primary} />
              <Text style={styles.upToDateText}>You're on the latest version</Text>
            </View>

            <ScrollView style={styles.changelogScroll} showsVerticalScrollIndicator={false}>
              {CHANGELOG.map((release, idx) => (
                <View key={release.version} style={[styles.releaseBlock, idx === CHANGELOG.length - 1 && { borderBottomWidth: 0 }]}>
                  <View style={styles.releaseHeader}>
                    <View style={styles.releaseVersionRow}>
                      <Text style={styles.releaseVersion}>v{release.version}</Text>
                      {release.label && (
                        <View style={[styles.releaseBadge, { backgroundColor: release.labelBg }]}>
                          <Text style={[styles.releaseBadgeText, { color: release.labelColor }]}>{release.label}</Text>
                        </View>
                      )}
                    </View>
                    <Text style={styles.releaseDate}>{release.date}</Text>
                  </View>
                  {release.changes.map((change, ci) => (
                    <View key={ci} style={styles.changeRow}>
                      <View style={styles.changeDot} />
                      <Text style={styles.changeText}>{change}</Text>
                    </View>
                  ))}
                </View>
              ))}
            </ScrollView>
          </View>
        </View>
      </Modal>

      {/* ─── FEEDBACK MODAL ─── */}
      <Modal visible={feedbackModalVisible} animationType="slide" transparent onRequestClose={closeFeedbackModal}>
        <KeyboardAvoidingView style={styles.modalOverlay} behavior={Platform.OS === 'ios' ? 'padding' : 'height'}>
          <View style={styles.modalSheet}>
            <View style={styles.sheetHandle} />

            {/* Header */}
            <View style={styles.modalHeader}>
              <View style={styles.modalHeaderLeft}>
                <View style={[styles.modalIconBox, { backgroundColor: C.secondaryContainer }]}>
                  <Ionicons name="chatbubble-ellipses" size={22} color={C.onSecondaryContainer} />
                </View>
                <View>
                  <Text style={styles.modalTitle}>Send Feedback</Text>
                  <Text style={styles.modalSubtitle}>We read every message</Text>
                </View>
              </View>
              <TouchableOpacity onPress={closeFeedbackModal} style={styles.closeBtn}>
                <Ionicons name="close" size={22} color={C.onSurfaceVariant} />
              </TouchableOpacity>
            </View>

            {submitted ? (
              /* Success State */
              <View style={styles.successWrap}>
                <View style={styles.successIconBox}>
                  <Ionicons name="checkmark-circle" size={56} color={C.primary} />
                </View>
                <Text style={styles.successTitle}>Thank you! 🎉</Text>
                <Text style={styles.successSubtitle}>Your feedback has been submitted. We'll review it and get back to you if needed.</Text>
                <TouchableOpacity style={styles.submitBtn} onPress={closeFeedbackModal}>
                  <Text style={styles.submitBtnText}>Done</Text>
                </TouchableOpacity>
              </View>
            ) : (
              <ScrollView keyboardShouldPersistTaps="handled" showsVerticalScrollIndicator={false}>
                {/* Type Selector */}
                <Text style={styles.fieldLabel}>What kind of feedback?</Text>
                <View style={styles.typeGrid}>
                  {FEEDBACK_TYPES.map(type => (
                    <TouchableOpacity
                      key={type.id}
                      style={[
                        styles.typeChip,
                        selectedType === type.id && { borderColor: type.color, backgroundColor: `${type.color}18` },
                      ]}
                      onPress={() => setSelectedType(type.id)}
                      activeOpacity={0.7}
                    >
                      <Text style={[styles.typeChipText, selectedType === type.id && { color: type.color, fontWeight: '700' }]}>
                        {type.label}
                      </Text>
                    </TouchableOpacity>
                  ))}
                </View>

                {/* Text Input */}
                <Text style={styles.fieldLabel}>Tell us more</Text>
                <TextInput
                  style={styles.textArea}
                  placeholder="Describe the issue, idea, or suggestion in detail..."
                  placeholderTextColor={C.outline}
                  multiline
                  numberOfLines={6}
                  textAlignVertical="top"
                  value={feedbackText}
                  onChangeText={setFeedbackText}
                  maxLength={500}
                />
                <Text style={styles.charCount}>{feedbackText.length}/500</Text>

                {/* Submit */}
                <TouchableOpacity
                  style={[styles.submitBtn, (submitting || !selectedType || !feedbackText.trim()) && styles.submitBtnDisabled]}
                  onPress={handleFeedbackSubmit}
                  activeOpacity={0.8}
                  disabled={submitting}
                >
                  {submitting ? (
                    <ActivityIndicator color="#fff" size="small" />
                  ) : (
                    <Text style={styles.submitBtnText}>Submit Feedback</Text>
                  )}
                </TouchableOpacity>

                <View style={{ height: 32 }} />
              </ScrollView>
            )}
          </View>
        </KeyboardAvoidingView>
      </Modal>
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
    backgroundColor: C.surfaceContainerHigh, borderWidth: 2, borderColor: 'rgba(0,107,27,0.1)',
  },
  headerAvatar: { width: '100%', height: '100%' },
  appBarTitle: { fontSize: 20, fontWeight: 'bold', fontStyle: 'italic', color: C.primary, letterSpacing: -0.5 },
  iconBtn: { padding: 4 },
  contentWrap: { paddingHorizontal: 24, paddingTop: 32, paddingBottom: 100 },
  profileSection: { alignItems: 'center', marginBottom: 40 },
  avatarMainWrap: { position: 'relative' },
  avatarMainBox: {
    width: 128, height: 128, borderRadius: 32, overflow: 'hidden',
    backgroundColor: C.surfaceContainerLow, shadowColor: '#000', shadowOpacity: 0.05, shadowRadius: 10, elevation: 2,
  },
  avatarMain: { width: '100%', height: '100%' },
  editBadge: {
    position: 'absolute', bottom: -8, right: -8, backgroundColor: C.primary,
    padding: 8, borderRadius: 16, shadowColor: '#000', shadowOpacity: 0.1, shadowRadius: 5, elevation: 3,
  },
  nameWrap: { alignItems: 'center', marginTop: 16 },
  userName: { fontSize: 28, fontWeight: '900', color: C.onSurface, letterSpacing: -0.5 },
  chefIdBadge: { backgroundColor: 'rgba(145,247,142,0.3)', paddingHorizontal: 12, paddingVertical: 4, borderRadius: 16, marginTop: 8 },
  chefIdText: { fontSize: 12, fontWeight: 'bold', color: C.primary },
  descSection: {
    backgroundColor: C.surfaceContainerLowest, borderRadius: 24, padding: 24,
    shadowColor: '#000', shadowOpacity: 0.02, shadowRadius: 10, elevation: 1, marginBottom: 24,
  },
  descHeader: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', marginBottom: 12 },
  descHeaderTitle: { fontSize: 16, fontWeight: 'bold', color: C.onSurface },
  descText: { fontSize: 14, color: C.onSurfaceVariant, lineHeight: 22 },
  editBioBtn: { flexDirection: 'row', alignItems: 'center', gap: 4, paddingHorizontal: 10, paddingVertical: 4, backgroundColor: C.surfaceContainerLow, borderRadius: 12 },
  editBioBtnText: { fontSize: 12, fontWeight: '600', color: C.onSurfaceVariant },
  bioEditWrap: { marginTop: 4 },
  bioInput: {
    backgroundColor: C.surfaceContainerLow, borderRadius: 12, padding: 12,
    fontSize: 14, color: C.onSurface, minHeight: 80, borderWidth: 1, borderColor: C.surfaceContainerHigh,
    lineHeight: 22,
  },
  bioActions: { flexDirection: 'row', justifyContent: 'flex-end', gap: 10, marginTop: 12 },
  bioCancelBtn: { paddingHorizontal: 16, paddingVertical: 8, borderRadius: 12, backgroundColor: C.surfaceContainerHigh },
  bioCancelText: { fontSize: 13, fontWeight: '600', color: C.onSurfaceVariant },
  bioSaveBtn: { paddingHorizontal: 20, paddingVertical: 8, borderRadius: 12, backgroundColor: C.primary, minWidth: 64, alignItems: 'center' },
  bioSaveText: { fontSize: 13, fontWeight: '700', color: '#fff' },

  actionsGrid: { gap: 16 },
  actionBtn: {
    flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between',
    backgroundColor: C.surfaceContainerLow, padding: 24, borderRadius: 24,
  },
  actionLogout: { backgroundColor: 'rgba(249,86,48,0.1)', borderWidth: 1, borderColor: 'rgba(249,86,48,0.2)' },
  actionLeft: { flexDirection: 'row', alignItems: 'center', gap: 16 },
  actionIconBox: { width: 44, height: 44, borderRadius: 12, alignItems: 'center', justifyContent: 'center' },
  actionTitle: { fontSize: 16, fontWeight: 'bold', color: C.onSurface, marginBottom: 2 },
  actionSubtitle: { fontSize: 12, color: C.onSurfaceVariant },
  appMeta: { alignItems: 'center', paddingVertical: 16, marginTop: 24 },
  metaText: { fontSize: 10, fontWeight: 'bold', color: C.outline, letterSpacing: 1 },

  // All Feedback modal
  fbLoadingWrap: { alignItems: 'center', justifyContent: 'center', paddingVertical: 48, gap: 12 },
  fbLoadingText: { fontSize: 14, color: C.onSurfaceVariant },
  fbEmptyText: { fontSize: 15, color: C.onSurfaceVariant, fontWeight: '600', marginTop: 8 },
  fbCard: {
    backgroundColor: C.surfaceContainerLow, borderRadius: 16, padding: 16, marginBottom: 12,
    borderWidth: 1, borderColor: C.surfaceContainerHigh,
  },
  fbCardTop: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', marginBottom: 6 },
  fbTypeBadge: { paddingHorizontal: 10, paddingVertical: 4, borderRadius: 10 },
  fbTypeBadgeText: { fontSize: 12, fontWeight: '700', textTransform: 'capitalize' },
  fbTime: { fontSize: 11, color: C.outline },
  fbUserName: { fontSize: 13, fontWeight: '700', color: C.onSurface, marginBottom: 4 },
  fbMessage: { fontSize: 13, color: C.onSurfaceVariant, lineHeight: 20 },

  // ── Modal shared ──
  modalOverlay: { flex: 1, justifyContent: 'flex-end', backgroundColor: 'rgba(0,0,0,0.4)' },
  modalSheet: {
    backgroundColor: C.surfaceContainerLowest, borderTopLeftRadius: 32, borderTopRightRadius: 32,
    paddingHorizontal: 24, paddingBottom: 40, maxHeight: '85%',
  },
  sheetHandle: {
    width: 40, height: 4, borderRadius: 2, backgroundColor: C.surfaceContainerHigh,
    alignSelf: 'center', marginTop: 12, marginBottom: 20,
  },
  modalHeader: {
    flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', marginBottom: 20,
  },
  modalHeaderLeft: { flexDirection: 'row', alignItems: 'center', gap: 14 },
  modalIconBox: { width: 48, height: 48, borderRadius: 14, alignItems: 'center', justifyContent: 'center' },
  modalTitle: { fontSize: 20, fontWeight: '900', color: C.onSurface, letterSpacing: -0.3 },
  modalSubtitle: { fontSize: 12, color: C.onSurfaceVariant, marginTop: 2 },
  closeBtn: {
    width: 36, height: 36, borderRadius: 18, backgroundColor: C.surfaceContainerLow,
    alignItems: 'center', justifyContent: 'center',
  },

  // ── Version Modal ──
  upToDateBadge: {
    flexDirection: 'row', alignItems: 'center', gap: 8, backgroundColor: 'rgba(145,247,142,0.2)',
    paddingHorizontal: 16, paddingVertical: 10, borderRadius: 12, marginBottom: 20,
  },
  upToDateText: { fontSize: 13, fontWeight: '600', color: C.primary },
  changelogScroll: { maxHeight: 420 },
  releaseBlock: {
    paddingVertical: 20, borderBottomWidth: 1, borderBottomColor: C.surfaceContainerHigh,
  },
  releaseHeader: { marginBottom: 12 },
  releaseVersionRow: { flexDirection: 'row', alignItems: 'center', gap: 10, marginBottom: 4 },
  releaseVersion: { fontSize: 17, fontWeight: '800', color: C.onSurface },
  releaseBadge: { paddingHorizontal: 10, paddingVertical: 3, borderRadius: 10 },
  releaseBadgeText: { fontSize: 11, fontWeight: '700' },
  releaseDate: { fontSize: 12, color: C.onSurfaceVariant },
  changeRow: { flexDirection: 'row', alignItems: 'flex-start', gap: 10, marginBottom: 6 },
  changeDot: {
    width: 6, height: 6, borderRadius: 3, backgroundColor: C.primary, marginTop: 7,
  },
  changeText: { flex: 1, fontSize: 14, color: C.onSurfaceVariant, lineHeight: 20 },

  // ── Feedback Modal ──
  fieldLabel: { fontSize: 14, fontWeight: '700', color: C.onSurface, marginBottom: 12 },
  typeGrid: { flexDirection: 'row', flexWrap: 'wrap', gap: 10, marginBottom: 24 },
  typeChip: {
    paddingHorizontal: 14, paddingVertical: 9, borderRadius: 20,
    borderWidth: 1.5, borderColor: C.surfaceContainerHigh, backgroundColor: C.surfaceContainerLow,
  },
  typeChipText: { fontSize: 13, fontWeight: '600', color: C.onSurfaceVariant },
  textArea: {
    backgroundColor: C.surfaceContainerLow, borderRadius: 16, padding: 16,
    fontSize: 14, color: C.onSurface, minHeight: 140, borderWidth: 1.5, borderColor: C.surfaceContainerHigh,
    lineHeight: 22,
  },
  charCount: { fontSize: 11, color: C.outline, textAlign: 'right', marginTop: 6, marginBottom: 20 },
  submitBtn: {
    backgroundColor: C.primary, borderRadius: 20, paddingVertical: 16,
    alignItems: 'center', justifyContent: 'center',
  },
  submitBtnDisabled: { opacity: 0.45 },
  submitBtnText: { fontSize: 16, fontWeight: '800', color: '#fff', letterSpacing: 0.2 },

  // Success
  successWrap: { alignItems: 'center', paddingVertical: 32, paddingHorizontal: 16 },
  successIconBox: { marginBottom: 16 },
  successTitle: { fontSize: 26, fontWeight: '900', color: C.onSurface, marginBottom: 10 },
  successSubtitle: { fontSize: 14, color: C.onSurfaceVariant, textAlign: 'center', lineHeight: 22, marginBottom: 32 },
});
