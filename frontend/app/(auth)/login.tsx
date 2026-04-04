import React, { useState } from 'react';
import { View, Text, TextInput, TouchableOpacity, StyleSheet, KeyboardAvoidingView, Platform, ScrollView, ActivityIndicator } from 'react-native';
import { useRouter } from 'expo-router';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { useAuth } from '@/context/AuthContext';
import { Colors, Spacing, Radius } from '@/constants/theme';
import { Ionicons } from '@expo/vector-icons';

export default function LoginScreen() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const [showPassword, setShowPassword] = useState(false);
  const { login } = useAuth();
  const router = useRouter();
  const insets = useSafeAreaInsets();

  const handleLogin = async () => {
    if (!email.trim() || !password) { setError('Please fill in all fields'); return; }
    setError('');
    setLoading(true);
    try {
      await login(email.trim(), password);
      router.replace('/(tabs)/home');
    } catch (e: any) {
      setError(e.message || 'Login failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <KeyboardAvoidingView style={styles.flex} behavior={Platform.OS === 'ios' ? 'padding' : 'height'}>
      <ScrollView contentContainerStyle={[styles.container, { paddingTop: insets.top + Spacing.xl }]} keyboardShouldPersistTaps="handled">
        <TouchableOpacity testID="login-back-btn" onPress={() => router.back()} style={styles.backBtn}>
          <Ionicons name="arrow-back" size={24} color={Colors.textPrimary} />
        </TouchableOpacity>

        <View style={styles.header}>
          <Text style={styles.title}>Welcome back</Text>
          <Text style={styles.subtitle}>Log in to your account</Text>
        </View>

        {error ? (
          <View style={styles.errorBox}>
            <Ionicons name="alert-circle" size={18} color={Colors.critical} />
            <Text testID="login-error" style={styles.errorText}>{error}</Text>
          </View>
        ) : null}

        <View style={styles.form}>
          <Text style={styles.label}>Email</Text>
          <TextInput
            testID="login-email-input"
            style={styles.input}
            placeholder="your@email.com"
            placeholderTextColor={Colors.expired}
            value={email}
            onChangeText={setEmail}
            keyboardType="email-address"
            autoCapitalize="none"
            autoCorrect={false}
          />

          <Text style={styles.label}>Password</Text>
          <View style={styles.passwordWrap}>
            <TextInput
              testID="login-password-input"
              style={[styles.input, { flex: 1, marginBottom: 0 }]}
              placeholder="Enter password"
              placeholderTextColor={Colors.expired}
              value={password}
              onChangeText={setPassword}
              secureTextEntry={!showPassword}
            />
            <TouchableOpacity testID="login-toggle-password" style={styles.eyeBtn} onPress={() => setShowPassword(!showPassword)}>
              <Ionicons name={showPassword ? 'eye-off' : 'eye'} size={22} color={Colors.textSecondary} />
            </TouchableOpacity>
          </View>
        </View>

        <TouchableOpacity testID="login-submit-btn" style={[styles.submitBtn, loading && styles.submitBtnDisabled]} onPress={handleLogin} disabled={loading} activeOpacity={0.8}>
          {loading ? <ActivityIndicator color={Colors.textInverse} /> : <Text style={styles.submitBtnText}>Log In</Text>}
        </TouchableOpacity>

        <TouchableOpacity testID="login-register-link" style={styles.linkBtn} onPress={() => router.replace('/(auth)/register')}>
          <Text style={styles.linkText}>Don't have an account? <Text style={styles.linkBold}>Sign up</Text></Text>
        </TouchableOpacity>
      </ScrollView>
    </KeyboardAvoidingView>
  );
}

const styles = StyleSheet.create({
  flex: { flex: 1, backgroundColor: Colors.bg },
  container: { flexGrow: 1, paddingHorizontal: Spacing.lg, paddingBottom: Spacing.xxl },
  backBtn: { width: 44, height: 44, justifyContent: 'center' },
  header: { marginTop: Spacing.lg, marginBottom: Spacing.xl },
  title: { fontSize: 34, fontWeight: '900', color: Colors.textPrimary, letterSpacing: -0.5 },
  subtitle: { fontSize: 16, color: Colors.textSecondary, marginTop: Spacing.xs },
  errorBox: { flexDirection: 'row', alignItems: 'center', gap: 8, backgroundColor: Colors.criticalBg, padding: Spacing.md, borderRadius: Radius.md, marginBottom: Spacing.md },
  errorText: { color: Colors.critical, fontSize: 14, flex: 1 },
  form: { marginBottom: Spacing.lg },
  label: { fontSize: 14, fontWeight: '600', color: Colors.textPrimary, marginBottom: Spacing.xs },
  input: { backgroundColor: Colors.inputBg, borderWidth: 1, borderColor: Colors.borderSubtle, borderRadius: Radius.lg, paddingHorizontal: 20, paddingVertical: 16, fontSize: 16, color: Colors.textPrimary, marginBottom: Spacing.md },
  passwordWrap: { flexDirection: 'row', alignItems: 'center', marginBottom: Spacing.md },
  eyeBtn: { position: 'absolute', right: 16, top: 16 },
  submitBtn: { backgroundColor: Colors.orange, borderRadius: Radius.full, paddingVertical: 16, alignItems: 'center', justifyContent: 'center' },
  submitBtnDisabled: { opacity: 0.7 },
  submitBtnText: { color: Colors.textInverse, fontSize: 18, fontWeight: '700' },
  linkBtn: { alignItems: 'center', marginTop: Spacing.lg },
  linkText: { color: Colors.textSecondary, fontSize: 15 },
  linkBold: { color: Colors.orange, fontWeight: '700' },
});
