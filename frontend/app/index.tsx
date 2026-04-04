import React from 'react';
import { View, Text, StyleSheet, TouchableOpacity, ActivityIndicator, ImageBackground } from 'react-native';
import { useRouter, Redirect } from 'expo-router';
import { useAuth } from '@/context/AuthContext';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { Colors, Spacing, Radius } from '@/constants/theme';
import { Ionicons } from '@expo/vector-icons';

export default function Onboarding() {
  const { user, loading } = useAuth();
  const router = useRouter();
  const insets = useSafeAreaInsets();

  if (loading) {
    return (
      <View style={[styles.loadingContainer]}>
        <ActivityIndicator size="large" color={Colors.orange} />
      </View>
    );
  }

  if (user) {
    return <Redirect href="/(tabs)/home" />;
  }

  return (
    <View style={styles.container}>
      <ImageBackground
        source={{ uri: 'https://static.prod-images.emergentagent.com/jobs/273815e5-780b-4e01-8072-0ebbf9ceebbd/images/9f3fc44ec4c71898d79a116a11fcd7f22a7bcda64696c0081eb5b5b7cb1953ce.png' }}
        style={styles.background}
        resizeMode="cover"
      >
        <View style={styles.overlay}>
          <View style={[styles.content, { paddingBottom: insets.bottom + Spacing.xl }]}>
            <View style={styles.iconRow}>
              <Ionicons name="flame" size={36} color={Colors.orange} />
            </View>
            <Text style={styles.title}>AI Recipe{'\n'}Generator</Text>
            <Text style={styles.subtitle}>
              Turn your ingredients into delicious meals with the power of AI
            </Text>
            <TouchableOpacity
              testID="get-started-btn"
              style={styles.primaryBtn}
              onPress={() => router.push('/(auth)/register')}
              activeOpacity={0.8}
            >
              <Text style={styles.primaryBtnText}>Get Started</Text>
              <Ionicons name="arrow-forward" size={20} color={Colors.textInverse} />
            </TouchableOpacity>
            <TouchableOpacity
              testID="login-link-btn"
              style={styles.secondaryBtn}
              onPress={() => router.push('/(auth)/login')}
              activeOpacity={0.7}
            >
              <Text style={styles.secondaryBtnText}>Already have an account? Log in</Text>
            </TouchableOpacity>
          </View>
        </View>
      </ImageBackground>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1 },
  loadingContainer: { flex: 1, justifyContent: 'center', alignItems: 'center', backgroundColor: Colors.bg },
  background: { flex: 1, width: '100%', height: '100%' },
  overlay: {
    flex: 1,
    backgroundColor: 'rgba(0,0,0,0.55)',
    justifyContent: 'flex-end',
  },
  content: { paddingHorizontal: Spacing.lg },
  iconRow: { marginBottom: Spacing.md },
  title: {
    fontSize: 42,
    fontWeight: '900',
    color: Colors.textInverse,
    letterSpacing: -1,
    lineHeight: 48,
    marginBottom: Spacing.md,
  },
  subtitle: {
    fontSize: 17,
    color: 'rgba(255,255,255,0.8)',
    lineHeight: 24,
    marginBottom: Spacing.xl,
  },
  primaryBtn: {
    backgroundColor: Colors.orange,
    borderRadius: Radius.full,
    paddingVertical: 16,
    paddingHorizontal: 32,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 8,
    marginBottom: Spacing.md,
  },
  primaryBtnText: { color: Colors.textInverse, fontSize: 18, fontWeight: '700' },
  secondaryBtn: { paddingVertical: 12, alignItems: 'center' },
  secondaryBtnText: { color: 'rgba(255,255,255,0.7)', fontSize: 15, fontWeight: '500' },
});
