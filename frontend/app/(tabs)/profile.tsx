import React, { useState } from 'react';
import { View, Text, StyleSheet, TouchableOpacity, ScrollView, TextInput, Alert } from 'react-native';
import { useRouter } from 'expo-router';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { useAuth } from '@/context/AuthContext';
import { Colors, Spacing, Radius } from '@/constants/theme';
import { Ionicons } from '@expo/vector-icons';

export default function ProfileScreen() {
  const insets = useSafeAreaInsets();
  const router = useRouter();
  const { user, logout, updateProfile } = useAuth();
  const [editAllergies, setEditAllergies] = useState(false);
  const [allergyInput, setAllergyInput] = useState('');
  const [allergies, setAllergies] = useState<string[]>(user?.allergies || []);
  const [saving, setSaving] = useState(false);

  const handleLogout = () => {
    Alert.alert('Logout', 'Are you sure you want to log out?', [
      { text: 'Cancel', style: 'cancel' },
      { text: 'Logout', style: 'destructive', onPress: async () => { await logout(); router.replace('/'); } },
    ]);
  };

  const addAllergy = () => {
    if (allergyInput.trim() && !allergies.includes(allergyInput.trim())) {
      setAllergies([...allergies, allergyInput.trim()]);
      setAllergyInput('');
    }
  };

  const removeAllergy = (a: string) => setAllergies(allergies.filter(x => x !== a));

  const saveAllergies = async () => {
    setSaving(true);
    try {
      await updateProfile({
        allergies: allergies.map(a => ({ allergen: a, severity: 'moderate' })),
      });
      setEditAllergies(false);
    } catch {} finally { setSaving(false); }
  };

  return (
    <ScrollView style={[styles.container, { paddingTop: insets.top }]} contentContainerStyle={styles.content}>
      <Text style={styles.title}>Profile</Text>

      <View style={styles.card}>
        <View style={styles.avatarCircle}>
          <Ionicons name="person" size={32} color={Colors.orange} />
        </View>
        <View style={styles.userInfo}>
          <Text style={styles.userName}>{user?.name}</Text>
          <Text style={styles.userEmail}>{user?.email}</Text>
        </View>
      </View>

      {/* Allergies */}
      <View style={styles.section}>
        <View style={styles.sectionHeader}>
          <Text style={styles.sectionTitle}>Allergies</Text>
          <TouchableOpacity testID="profile-edit-allergies" onPress={() => setEditAllergies(!editAllergies)}>
            <Ionicons name={editAllergies ? 'close' : 'create-outline'} size={22} color={Colors.orange} />
          </TouchableOpacity>
        </View>

        {allergies.length > 0 ? (
          <View style={styles.chipWrap}>
            {allergies.map(a => (
              <View key={a} style={[styles.chip, styles.allergyChip]}>
                <Text style={styles.allergyChipText}>{a}</Text>
                {editAllergies && (
                  <TouchableOpacity onPress={() => removeAllergy(a)}>
                    <Ionicons name="close" size={14} color={Colors.critical} />
                  </TouchableOpacity>
                )}
              </View>
            ))}
          </View>
        ) : (
          <Text style={styles.emptyText}>No allergies set</Text>
        )}

        {editAllergies && (
          <View style={styles.addRow}>
            <TextInput testID="profile-allergy-input" style={[styles.input, { flex: 1 }]} placeholder="e.g. Peanuts" placeholderTextColor={Colors.expired} value={allergyInput} onChangeText={setAllergyInput} onSubmitEditing={addAllergy} />
            <TouchableOpacity testID="profile-add-allergy" style={styles.addBtn} onPress={addAllergy}>
              <Ionicons name="add" size={22} color={Colors.textInverse} />
            </TouchableOpacity>
          </View>
        )}

        {editAllergies && (
          <TouchableOpacity testID="profile-save-allergies" style={[styles.saveBtn, saving && { opacity: 0.7 }]} onPress={saveAllergies} disabled={saving}>
            <Text style={styles.saveBtnText}>{saving ? 'Saving...' : 'Save Allergies'}</Text>
          </TouchableOpacity>
        )}
      </View>

      {/* Preferences */}
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>Dietary Preferences</Text>
        <View style={styles.chipWrap}>
          {(user?.dietary_preferences || []).length > 0 ? (
            (user?.dietary_preferences || []).map((p: string) => (
              <View key={p} style={styles.chip}><Text style={styles.chipText}>{p}</Text></View>
            ))
          ) : (
            <Text style={styles.emptyText}>None set</Text>
          )}
        </View>
      </View>

      <TouchableOpacity testID="profile-logout-btn" style={styles.logoutBtn} onPress={handleLogout}>
        <Ionicons name="log-out-outline" size={22} color={Colors.critical} />
        <Text style={styles.logoutText}>Log Out</Text>
      </TouchableOpacity>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: Colors.bg },
  content: { paddingHorizontal: Spacing.lg, paddingBottom: Spacing.xxl },
  title: { fontSize: 28, fontWeight: '900', color: Colors.textPrimary, marginTop: Spacing.md, marginBottom: Spacing.lg },
  card: { flexDirection: 'row', alignItems: 'center', backgroundColor: Colors.card, borderRadius: Radius.xxl, padding: Spacing.lg, borderWidth: 1, borderColor: Colors.borderSubtle, marginBottom: Spacing.lg },
  avatarCircle: { width: 56, height: 56, borderRadius: 28, backgroundColor: Colors.inputBg, alignItems: 'center', justifyContent: 'center' },
  userInfo: { marginLeft: Spacing.md, flex: 1 },
  userName: { fontSize: 20, fontWeight: '800', color: Colors.textPrimary },
  userEmail: { fontSize: 14, color: Colors.textSecondary, marginTop: 2 },
  section: { marginBottom: Spacing.lg },
  sectionHeader: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', marginBottom: Spacing.sm },
  sectionTitle: { fontSize: 17, fontWeight: '700', color: Colors.textPrimary },
  chipWrap: { flexDirection: 'row', flexWrap: 'wrap', gap: 8 },
  chip: { paddingHorizontal: 14, paddingVertical: 8, borderRadius: Radius.full, backgroundColor: Colors.inputBg, flexDirection: 'row', alignItems: 'center', gap: 6 },
  chipText: { fontSize: 14, color: Colors.textSecondary, fontWeight: '600' },
  allergyChip: { backgroundColor: Colors.criticalBg, borderWidth: 1, borderColor: Colors.critical },
  allergyChipText: { fontSize: 14, color: Colors.critical, fontWeight: '600' },
  emptyText: { fontSize: 14, color: Colors.expired },
  addRow: { flexDirection: 'row', gap: Spacing.sm, marginTop: Spacing.sm },
  input: { backgroundColor: Colors.inputBg, borderWidth: 1, borderColor: Colors.borderSubtle, borderRadius: Radius.md, paddingHorizontal: 16, paddingVertical: 14, fontSize: 16, color: Colors.textPrimary },
  addBtn: { backgroundColor: Colors.orange, width: 48, borderRadius: Radius.md, alignItems: 'center', justifyContent: 'center' },
  saveBtn: { backgroundColor: Colors.orange, borderRadius: Radius.full, paddingVertical: 14, alignItems: 'center', marginTop: Spacing.md },
  saveBtnText: { color: Colors.textInverse, fontSize: 16, fontWeight: '700' },
  logoutBtn: { flexDirection: 'row', alignItems: 'center', justifyContent: 'center', gap: 8, paddingVertical: 16, backgroundColor: Colors.criticalBg, borderRadius: Radius.full, marginTop: Spacing.lg },
  logoutText: { color: Colors.critical, fontSize: 16, fontWeight: '700' },
});
