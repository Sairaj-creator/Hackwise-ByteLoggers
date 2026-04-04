import React, { useEffect, useState, useCallback } from 'react';
import { View, Text, StyleSheet, TouchableOpacity, ScrollView, RefreshControl, Image } from 'react-native';
import { useRouter } from 'expo-router';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { useAuth } from '@/context/AuthContext';
import { api } from '@/services/api';
import { Colors, Spacing, Radius, PLACEHOLDER_IMAGES } from '@/constants/theme';
import { Ionicons } from '@expo/vector-icons';

export default function HomeScreen() {
  const { user } = useAuth();
  const router = useRouter();
  const insets = useSafeAreaInsets();
  const [fridgeData, setFridgeData] = useState<any>(null);
  const [recipes, setRecipes] = useState<any[]>([]);
  const [refreshing, setRefreshing] = useState(false);

  const loadData = useCallback(async () => {
    try {
      const [fridge, recipeData] = await Promise.all([api.getFridge(), api.getMyRecipes()]);
      setFridgeData(fridge);
      setRecipes(recipeData.recipes || []);
    } catch {}
  }, []);

  useEffect(() => { loadData(); }, [loadData]);

  const onRefresh = async () => { setRefreshing(true); await loadData(); setRefreshing(false); };

  const greeting = () => {
    const h = new Date().getHours();
    if (h < 12) return 'Good morning';
    if (h < 17) return 'Good afternoon';
    return 'Good evening';
  };

  return (
    <ScrollView
      style={[styles.container, { paddingTop: insets.top }]}
      contentContainerStyle={styles.content}
      refreshControl={<RefreshControl refreshing={refreshing} onRefresh={onRefresh} tintColor={Colors.orange} />}
    >
      <View style={styles.greetingRow}>
        <View style={{ flex: 1 }}>
          <Text style={styles.greeting}>{greeting()},</Text>
          <Text style={styles.userName}>{user?.name || 'Chef'}</Text>
        </View>
        <TouchableOpacity testID="home-profile-btn" onPress={() => router.push('/(tabs)/profile')} style={styles.avatarBtn}>
          <Ionicons name="person-circle" size={44} color={Colors.orange} />
        </TouchableOpacity>
      </View>

      {/* Quick Generate CTA */}
      <TouchableOpacity testID="home-generate-btn" style={styles.generateCard} onPress={() => router.push('/(tabs)/generate')} activeOpacity={0.85}>
        <View style={styles.generateContent}>
          <Ionicons name="sparkles" size={28} color={Colors.textInverse} />
          <Text style={styles.generateTitle}>Generate a Recipe</Text>
          <Text style={styles.generateSub}>Let AI create something delicious from your ingredients</Text>
        </View>
        <Ionicons name="arrow-forward-circle" size={36} color="rgba(255,255,255,0.8)" />
      </TouchableOpacity>

      {/* Fridge Summary */}
      <View style={styles.statsRow}>
        <TouchableOpacity testID="home-fridge-card" style={styles.statCard} onPress={() => router.push('/(tabs)/fridge')}>
          <Ionicons name="basket" size={24} color={Colors.fresh} />
          <Text style={styles.statNumber}>{fridgeData?.total || 0}</Text>
          <Text style={styles.statLabel}>In Fridge</Text>
        </TouchableOpacity>
        <TouchableOpacity testID="home-expiring-card" style={[styles.statCard, fridgeData?.expiring_soon_count > 0 && styles.statCardWarning]} onPress={() => router.push('/(tabs)/fridge')}>
          <Ionicons name="alert-circle" size={24} color={fridgeData?.expiring_soon_count > 0 ? Colors.warning : Colors.expired} />
          <Text style={styles.statNumber}>{fridgeData?.expiring_soon_count || 0}</Text>
          <Text style={styles.statLabel}>Expiring Soon</Text>
        </TouchableOpacity>
        <TouchableOpacity testID="home-recipes-card" style={styles.statCard} onPress={() => router.push('/(tabs)/favorites')}>
          <Ionicons name="restaurant" size={24} color={Colors.orange} />
          <Text style={styles.statNumber}>{recipes.length}</Text>
          <Text style={styles.statLabel}>Recipes</Text>
        </TouchableOpacity>
      </View>

      {/* Recent Recipes */}
      {recipes.length > 0 && (
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Recent Recipes</Text>
          {recipes.slice(0, 5).map((recipe, i) => (
            <TouchableOpacity
              key={recipe.recipe_id}
              testID={`home-recipe-${i}`}
              style={styles.recipeItem}
              onPress={() => router.push(`/recipe/${recipe.recipe_id}`)}
            >
              <Image source={{ uri: PLACEHOLDER_IMAGES[i % PLACEHOLDER_IMAGES.length] }} style={styles.recipeThumb} />
              <View style={styles.recipeInfo}>
                <Text style={styles.recipeName} numberOfLines={1}>{recipe.title}</Text>
                <View style={styles.recipeMeta}>
                  <Ionicons name="time-outline" size={14} color={Colors.textSecondary} />
                  <Text style={styles.recipeMetaText}>{recipe.total_time_minutes || recipe.cook_time_minutes || '?'} min</Text>
                  <Ionicons name="flame-outline" size={14} color={Colors.textSecondary} />
                  <Text style={styles.recipeMetaText}>{recipe.difficulty || 'Easy'}</Text>
                </View>
              </View>
              <Ionicons name="chevron-forward" size={20} color={Colors.expired} />
            </TouchableOpacity>
          ))}
        </View>
      )}

      {recipes.length === 0 && (
        <View style={styles.emptySection}>
          <Image source={{ uri: 'https://images.unsplash.com/photo-1573246123716-6b1782bfc499?crop=entropy&cs=srgb&fm=jpg&ixid=M3w3NTY2NzR8MHwxfHNlYXJjaHwzfHxmcmVzaCUyMHZlZ2V0YWJsZXMlMjBjb29raW5nJTIwZmxhdGxheXxlbnwwfHx8fDE3NzUzMTM5NTd8MA&ixlib=rb-4.1.0&q=85' }} style={styles.emptyImage} />
          <Text style={styles.emptyTitle}>No recipes yet</Text>
          <Text style={styles.emptyText}>Add ingredients to your fridge and let AI create amazing recipes for you!</Text>
        </View>
      )}
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: Colors.bg },
  content: { paddingHorizontal: Spacing.lg, paddingBottom: Spacing.xxl },
  greetingRow: { flexDirection: 'row', alignItems: 'center', marginTop: Spacing.md, marginBottom: Spacing.lg },
  greeting: { fontSize: 15, color: Colors.textSecondary, fontWeight: '500' },
  userName: { fontSize: 26, fontWeight: '900', color: Colors.textPrimary, letterSpacing: -0.5 },
  avatarBtn: { width: 48, height: 48, alignItems: 'center', justifyContent: 'center' },
  generateCard: {
    backgroundColor: Colors.orange,
    borderRadius: Radius.xxl,
    padding: Spacing.lg,
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: Spacing.lg,
  },
  generateContent: { flex: 1 },
  generateTitle: { fontSize: 20, fontWeight: '800', color: Colors.textInverse, marginTop: Spacing.sm },
  generateSub: { fontSize: 13, color: 'rgba(255,255,255,0.8)', marginTop: Spacing.xs },
  statsRow: { flexDirection: 'row', gap: Spacing.sm, marginBottom: Spacing.lg },
  statCard: {
    flex: 1,
    backgroundColor: Colors.card,
    borderRadius: Radius.xl,
    padding: Spacing.md,
    alignItems: 'center',
    borderWidth: 1,
    borderColor: Colors.borderSubtle,
  },
  statCardWarning: { borderColor: Colors.warning, backgroundColor: Colors.warningBg },
  statNumber: { fontSize: 24, fontWeight: '900', color: Colors.textPrimary, marginTop: Spacing.xs },
  statLabel: { fontSize: 11, color: Colors.textSecondary, fontWeight: '600', marginTop: 2 },
  section: { marginBottom: Spacing.lg },
  sectionTitle: { fontSize: 20, fontWeight: '800', color: Colors.textPrimary, marginBottom: Spacing.md },
  recipeItem: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: Colors.card,
    borderRadius: Radius.xl,
    padding: Spacing.sm,
    marginBottom: Spacing.sm,
    borderWidth: 1,
    borderColor: Colors.borderSubtle,
  },
  recipeThumb: { width: 56, height: 56, borderRadius: Radius.md },
  recipeInfo: { flex: 1, marginLeft: Spacing.md },
  recipeName: { fontSize: 15, fontWeight: '700', color: Colors.textPrimary },
  recipeMeta: { flexDirection: 'row', alignItems: 'center', gap: 4, marginTop: 4 },
  recipeMetaText: { fontSize: 12, color: Colors.textSecondary, marginRight: 8 },
  emptySection: { alignItems: 'center', paddingVertical: Spacing.xl },
  emptyImage: { width: 200, height: 140, borderRadius: Radius.xl, marginBottom: Spacing.md },
  emptyTitle: { fontSize: 18, fontWeight: '700', color: Colors.textPrimary },
  emptyText: { fontSize: 14, color: Colors.textSecondary, textAlign: 'center', marginTop: Spacing.xs, paddingHorizontal: Spacing.lg },
});
