import React, { useEffect, useState, useCallback } from 'react';
import { View, Text, StyleSheet, TouchableOpacity, ScrollView, RefreshControl, Image, ActivityIndicator } from 'react-native';
import { useRouter } from 'expo-router';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { useAuth } from '@/context/AuthContext';
import { api } from '@/services/api';
import { PLACEHOLDER_IMAGES } from '@/constants/theme';
import { Ionicons, MaterialCommunityIcons } from '@expo/vector-icons';

const C = {
  surface: '#f6f6f6',
  onSurface: '#2d2f2f',
  onSurfaceVariant: '#5a5c5c',
  primary: '#006b1b',
  onPrimary: '#d1ffc8',
  secondary: '#874e00',
  tertiary: '#3c6600',
  surfaceLowest: '#ffffff',
  surfaceLow: '#f0f1f1',
  tertiaryContainer: '#c1fd7c',
  onTertiaryContainer: '#396100',
  secondaryContainer: '#ffc791',
  onSecondaryContainer: '#6a3c00',
  primaryContainer: '#91f78e',
  onPrimaryContainer: '#005e17',
  outlineVariant: '#acadad',
};

export default function HomeScreen() {
  const { user } = useAuth();
  const router = useRouter();
  const insets = useSafeAreaInsets();
  const [fridgeData, setFridgeData] = useState<any>(null);
  const [myRecipes, setMyRecipes] = useState<any[]>([]);
  const [trendingRecipes, setTrendingRecipes] = useState<any[]>([]);
  const [location, setLocation] = useState<string>('Detecting...');
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  const loadData = useCallback(async () => {
    try {
      const loc = await api.getUserLocation();
      setLocation(loc);

      const [fridge, recipeData, trendingData] = await Promise.allSettled([
        api.getFridge(),
        api.getMyRecipes(),
        api.getTrendingRecipes(loc),
      ]);

      if (fridge.status === 'fulfilled') setFridgeData(fridge.value);
      if (recipeData.status === 'fulfilled') setMyRecipes(recipeData.value.recipes || []);
      if (trendingData.status === 'fulfilled') setTrendingRecipes(trendingData.value.recipes || []);
    } catch (e) {
      console.log('Home load error:', e);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { loadData(); }, [loadData]);

  const onRefresh = async () => { setRefreshing(true); await loadData(); setRefreshing(false); };

  const fridgeCount = fridgeData?.ingredients?.length ?? 0;

  if (loading) {
    return (
      <View style={[styles.container, { paddingTop: insets.top, justifyContent: 'center', alignItems: 'center' }]}>
        <ActivityIndicator size="large" color={C.primary} />
        <Text style={{ color: C.onSurfaceVariant, marginTop: 12, fontSize: 14 }}>Loading your kitchen...</Text>
      </View>
    );
  }

  return (
    <View style={[styles.container, { paddingTop: insets.top }]}>
      {/* Header */}
      <View style={styles.header}>
        <TouchableOpacity style={styles.iconBtn} onPress={() => router.push('/(tabs)/profile')}>
          <Ionicons name="menu" size={24} color={C.primary} />
        </TouchableOpacity>
        <View style={{ flexDirection: 'row', alignItems: 'center', gap: 6 }}>
          <MaterialCommunityIcons name="chef-hat" size={24} color={C.primary} />
          <Text style={styles.headerTitle}>Ingredia</Text>
        </View>
        <TouchableOpacity testID="home-profile-btn" onPress={() => router.push('/(tabs)/profile')} style={styles.avatarBorder}>
          <Image source={{ uri: 'https://lh3.googleusercontent.com/aida-public/AB6AXuB0Nec5iT3xElO0fPegZ3Dve3Zdw37EGdjVzwrpaYx1_xsIIwE8Y7pTUtz9yFbe18Ak-BpPCsB556uwM2LY_HXvj9PvnrQK6z2kCE8rSN8KQKCz0K6fqxDBAQ5wDD_LNdIF6NUkHzNacyd4mqL6AfV5Z9A16eW8BiuGEOGm_pVMulebrP_5B4nyVYkf_6VeyOYxjAWgHkPsW5h7wlpu5wdMSlUlEE7xAQ8Yk30zsiQ8dkN89Lp46KeYjdXCNSTprQOTkqybeLPgNZwm' }} style={styles.avatar} />
        </TouchableOpacity>
      </View>

      <ScrollView
        contentContainerStyle={styles.content}
        refreshControl={<RefreshControl refreshing={refreshing} onRefresh={onRefresh} tintColor={C.primary} />}
        showsVerticalScrollIndicator={false}
      >
        {/* Welcome Section */}
        <View style={styles.welcomeSection}>
          <View style={styles.locationRow}>
            <Ionicons name="location" size={14} color={C.tertiary} />
            <Text style={styles.locationText}>LOCATION: {location.toUpperCase()}</Text>
          </View>
          <Text style={styles.welcomeTitle}>
            {user?.name ? `${user.name}'s\nIngredia AI Kitchen` : 'Ingredia AI Kitchen'}
          </Text>
          <Text style={styles.welcomeSub}>
            Curated flavors and intelligent pairings, tailored to your available ingredients.
          </Text>
          {/* Fridge quick status */}
          <View style={styles.fridgeStatusRow}>
            <View style={styles.fridgeStatusChip}>
              <Ionicons name="cube-outline" size={14} color={C.primary} />
              <Text style={styles.fridgeStatusText}>{fridgeCount} ingredients in fridge</Text>
            </View>
            {fridgeCount === 0 && (
              <TouchableOpacity onPress={() => router.push('/(tabs)/fridge')} style={styles.addFridgeChip}>
                <Text style={styles.addFridgeText}>Add ingredients</Text>
                <Ionicons name="arrow-forward" size={13} color={C.primary} />
              </TouchableOpacity>
            )}
          </View>
        </View>

        {/* ─── YOUR AI RECIPES SECTION ─── */}
        <View style={styles.sectionHeader}>
          <Text style={styles.editorChoice}>AI CHEF PICKS</Text>
          <Text style={styles.sectionTitle}>Your Recipes</Text>
        </View>

        {myRecipes.length === 0 ? (
          <View style={styles.emptyRecipeCard}>
            <Ionicons name="sparkles-outline" size={44} color={C.outlineVariant} />
            <Text style={styles.emptyRecipeTitle}>No recipes generated yet</Text>
            <Text style={styles.emptyRecipeSub}>
              Add ingredients to your fridge and generate your first AI recipe.
            </Text>
            <TouchableOpacity style={styles.generateBtn} onPress={() => router.push('/(tabs)/generate')}>
              <Ionicons name="sparkles" size={16} color={C.onPrimary} />
              <Text style={styles.generateBtnText}>Generate a Recipe</Text>
            </TouchableOpacity>
          </View>
        ) : (
          <>
            {/* Hero recipe card */}
            <View style={styles.heroCard}>
              <View style={styles.heroImageContainer}>
                <Image
                  source={{ uri: myRecipes[0].image_url || PLACEHOLDER_IMAGES[(myRecipes[0].title?.length || 0) % PLACEHOLDER_IMAGES.length] }}
                  style={styles.heroImage}
                />
                <View style={styles.aiBadge}>
                  <Ionicons name="sparkles" size={12} color={C.primary} />
                  <Text style={styles.aiBadgeText}>AI GENERATED</Text>
                </View>
              </View>
              <View style={styles.heroContent}>
                <Text style={styles.heroTitle}>{myRecipes[0].title}</Text>
                <Text style={styles.heroSub} numberOfLines={2}>
                  {myRecipes[0].description || `A ${myRecipes[0].cuisine || 'delicious'} recipe crafted from your ingredients.`}
                </Text>
                <View style={styles.heroMetaRow}>
                  <View style={styles.metaBadge}>
                    <Ionicons name="time-outline" size={14} color={C.secondary} />
                    <Text style={styles.metaText}>{myRecipes[0].estimated_time_minutes || 30} MIN</Text>
                  </View>
                  <View style={styles.metaBadge}>
                    <Ionicons name="flame-outline" size={14} color={C.secondary} />
                    <Text style={styles.metaText}>{myRecipes[0].difficulty || 'Easy'}</Text>
                  </View>
                  {myRecipes[0].cuisine ? (
                    <View style={styles.metaBadge}>
                      <Ionicons name="restaurant-outline" size={14} color={C.secondary} />
                      <Text style={styles.metaText}>{myRecipes[0].cuisine}</Text>
                    </View>
                  ) : null}
                </View>
                <TouchableOpacity style={styles.heroBtn} onPress={() => router.push(`/recipe/${myRecipes[0].recipe_id}`)}>
                  <Text style={styles.heroBtnText}>View Recipe</Text>
                  <Ionicons name="arrow-forward" size={16} color={C.onPrimary} />
                </TouchableOpacity>
              </View>
            </View>

            {/* Grid of remaining recipes */}
            {myRecipes.length > 1 && (
              <View style={styles.grid}>
                {myRecipes.slice(1, 5).map((recipe, i) => (
                  <TouchableOpacity
                    key={recipe.recipe_id || recipe.id}
                    style={styles.gridCard}
                    onPress={() => router.push(`/recipe/${recipe.recipe_id}`)}
                  >
                    <View style={styles.gridImageContainer}>
                      <Image
                        source={{ uri: recipe.image_url || PLACEHOLDER_IMAGES[((recipe.title?.length || 0) + i) % PLACEHOLDER_IMAGES.length] }}
                        style={styles.gridImage}
                      />
                    </View>
                    <View style={styles.gridContent}>
                      <Text style={styles.gridTitle} numberOfLines={2}>{recipe.title}</Text>
                      <View style={styles.gridTags}>
                        <View style={[styles.gridTag, { backgroundColor: C.secondaryContainer }]}>
                          <Text style={[styles.gridTagText, { color: C.onSecondaryContainer }]}>
                            {recipe.difficulty?.toUpperCase() || 'EASY'}
                          </Text>
                        </View>
                        <View style={[styles.gridTag, { backgroundColor: C.primaryContainer }]}>
                          <Text style={[styles.gridTagText, { color: C.onPrimaryContainer }]}>
                            {recipe.estimated_time_minutes || 20} MIN
                          </Text>
                        </View>
                      </View>
                    </View>
                  </TouchableOpacity>
                ))}
              </View>
            )}

            {myRecipes.length > 5 && (
              <TouchableOpacity style={styles.seeAllBtn} onPress={() => router.push('/(tabs)/generate')}>
                <Text style={styles.seeAllText}>See all {myRecipes.length} recipes</Text>
                <Ionicons name="arrow-forward" size={16} color={C.primary} />
              </TouchableOpacity>
            )}
          </>
        )}

        {/* ─── LOCAL TRENDS SECTION ─── */}
        {trendingRecipes.length > 0 && (
          <>
            <View style={[styles.sectionHeader, { marginTop: 32 }]}>
              <Text style={styles.editorChoice}>LOCAL TRENDS</Text>
              <Text style={styles.sectionTitle}>Trending in {location}</Text>
            </View>

            <ScrollView
              horizontal
              showsHorizontalScrollIndicator={false}
              contentContainerStyle={styles.trendRow}
            >
              {trendingRecipes.map((recipe, i) => (
                <TouchableOpacity
                  key={recipe.recipe_id || `trend-${i}`}
                  style={styles.trendCard}
                  onPress={() => router.push(`/recipe/${recipe.recipe_id}`)}
                  activeOpacity={0.85}
                >
                  <Image
                    source={{ uri: PLACEHOLDER_IMAGES[((recipe.title?.length || 0) + i) % PLACEHOLDER_IMAGES.length] }}
                    style={styles.trendCardImage}
                  />
                  <View style={styles.trendCardOverlay} />
                  <View style={styles.trendCardContent}>
                    <Text style={styles.trendCardTitle} numberOfLines={2}>{recipe.title}</Text>
                    <View style={styles.trendCardMeta}>
                      <Ionicons name="time-outline" size={12} color="rgba(255,255,255,0.8)" />
                      <Text style={styles.trendCardMetaText}>
                        {recipe.total_time_minutes || recipe.estimated_time_minutes || 30} min
                      </Text>
                      <Text style={styles.trendCardMetaText}>· {recipe.cuisine || recipe.difficulty || 'Local'}</Text>
                    </View>
                  </View>
                </TouchableOpacity>
              ))}
            </ScrollView>
          </>
        )}

        {/* AI Assistant Banner */}
        <View style={[styles.aiBanner, { marginTop: 32 }]}>
          <View style={styles.aiBannerBg}>
            <Ionicons name="sparkles" size={160} color="rgba(255,255,255,0.05)" style={styles.aiBannerIcon} />
          </View>
          <View style={styles.aiBannerContent}>
            <Text style={styles.aiBannerTitle}>What's in your fridge?</Text>
            <Text style={styles.aiBannerSub}>
              Snap a photo and let our AI curate a recipe from your available ingredients.
            </Text>
            <TouchableOpacity style={styles.aiBannerBtn} onPress={() => router.push('/(tabs)/generate')}>
              <Text style={styles.aiBannerBtnText}>Generate Recipe</Text>
            </TouchableOpacity>
          </View>
        </View>

      </ScrollView>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: C.surface },
  header: {
    flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center',
    paddingHorizontal: 24, paddingVertical: 16, backgroundColor: C.surface,
  },
  iconBtn: { padding: 4 },
  headerTitle: { fontSize: 20, fontWeight: 'bold', fontStyle: 'italic', color: C.primary },
  avatarBorder: {
    width: 40, height: 40, borderRadius: 20,
    borderWidth: 2, borderColor: C.primaryContainer, overflow: 'hidden',
  },
  avatar: { width: '100%', height: '100%' },
  content: { paddingHorizontal: 24, paddingBottom: 100 },

  welcomeSection: { marginTop: 16, marginBottom: 32 },
  locationRow: { flexDirection: 'row', alignItems: 'center', gap: 4, marginBottom: 8 },
  locationText: { fontSize: 12, fontWeight: '600', color: C.tertiary, letterSpacing: 0.5 },
  welcomeTitle: { fontSize: 32, fontWeight: '900', color: C.onSurface, lineHeight: 40, marginBottom: 8 },
  welcomeSub: { fontSize: 15, color: C.onSurfaceVariant, lineHeight: 22, maxWidth: '90%', marginBottom: 16 },
  fridgeStatusRow: { flexDirection: 'row', alignItems: 'center', gap: 10, flexWrap: 'wrap' },
  fridgeStatusChip: {
    flexDirection: 'row', alignItems: 'center', gap: 6,
    backgroundColor: 'rgba(0,107,27,0.08)', paddingHorizontal: 12, paddingVertical: 6, borderRadius: 20,
  },
  fridgeStatusText: { fontSize: 12, fontWeight: '600', color: C.primary },
  addFridgeChip: {
    flexDirection: 'row', alignItems: 'center', gap: 4,
    backgroundColor: C.secondaryContainer, paddingHorizontal: 12, paddingVertical: 6, borderRadius: 20,
  },
  addFridgeText: { fontSize: 12, fontWeight: '600', color: C.onSecondaryContainer },

  sectionHeader: { marginBottom: 20 },
  editorChoice: { fontSize: 12, fontWeight: '700', color: C.secondary, letterSpacing: 1.5, marginBottom: 4 },
  sectionTitle: { fontSize: 24, fontWeight: 'bold', color: C.onSurface },

  emptyRecipeCard: {
    backgroundColor: C.surfaceLowest, borderRadius: 24, padding: 32,
    alignItems: 'center', gap: 10,
    borderWidth: 2, borderStyle: 'dashed', borderColor: C.outlineVariant,
    marginBottom: 32,
  },
  emptyRecipeTitle: { fontSize: 18, fontWeight: 'bold', color: C.onSurface },
  emptyRecipeSub: { fontSize: 13, color: C.onSurfaceVariant, textAlign: 'center', lineHeight: 20 },
  generateBtn: {
    flexDirection: 'row', alignItems: 'center', gap: 8,
    backgroundColor: C.primary, paddingHorizontal: 20, paddingVertical: 12, borderRadius: 12, marginTop: 8,
  },
  generateBtnText: { color: C.onPrimary, fontSize: 14, fontWeight: 'bold' },

  heroCard: {
    backgroundColor: C.surfaceLowest, borderRadius: 24, overflow: 'hidden', marginBottom: 24,
    shadowColor: C.onSurface, shadowOffset: { width: 0, height: 8 }, shadowOpacity: 0.06, shadowRadius: 24, elevation: 4,
  },
  heroImageContainer: { height: 220, width: '100%', position: 'relative' },
  heroImage: { width: '100%', height: '100%' },
  aiBadge: {
    position: 'absolute', top: 16, left: 16,
    backgroundColor: 'rgba(255,255,255,0.92)',
    flexDirection: 'row', alignItems: 'center', gap: 4,
    paddingHorizontal: 10, paddingVertical: 6, borderRadius: 16,
  },
  aiBadgeText: { fontSize: 10, fontWeight: '800', color: C.primary },
  heroContent: { padding: 20, gap: 10 },
  heroTitle: { fontSize: 22, fontWeight: 'bold', color: C.onSurface },
  heroSub: { fontSize: 14, color: C.onSurfaceVariant, lineHeight: 20 },
  heroMetaRow: {
    flexDirection: 'row', gap: 16, flexWrap: 'wrap',
    paddingVertical: 10, borderTopWidth: 1, borderBottomWidth: 1,
    borderColor: 'rgba(172,173,173,0.2)',
  },
  metaBadge: { flexDirection: 'row', alignItems: 'center', gap: 6 },
  metaText: { fontSize: 12, fontWeight: '600', color: C.onSurface },
  heroBtn: {
    backgroundColor: C.primary, flexDirection: 'row', alignItems: 'center',
    justifyContent: 'center', gap: 8, paddingVertical: 14, borderRadius: 12, marginTop: 4,
  },
  heroBtnText: { color: C.onPrimary, fontSize: 16, fontWeight: 'bold' },

  grid: { flexDirection: 'row', flexWrap: 'wrap', justifyContent: 'space-between', marginBottom: 16 },
  gridCard: {
    width: '48%', backgroundColor: C.surfaceLow, borderRadius: 20,
    padding: 12, marginBottom: 16, overflow: 'hidden',
  },
  gridImageContainer: { width: '100%', aspectRatio: 1.2, borderRadius: 12, overflow: 'hidden', marginBottom: 10 },
  gridImage: { width: '100%', height: '100%' },
  gridContent: { gap: 8 },
  gridTitle: { fontSize: 14, fontWeight: 'bold', color: C.onSurface },
  gridTags: { flexDirection: 'row', flexWrap: 'wrap', gap: 6 },
  gridTag: { paddingHorizontal: 8, paddingVertical: 3, borderRadius: 6 },
  gridTagText: { fontSize: 9, fontWeight: 'bold', textTransform: 'uppercase' },

  seeAllBtn: {
    flexDirection: 'row', alignItems: 'center', justifyContent: 'center', gap: 6,
    paddingVertical: 12, marginBottom: 8,
  },
  seeAllText: { fontSize: 14, fontWeight: '700', color: C.primary },

  trendRow: { paddingBottom: 8, gap: 16 },
  trendCard: {
    width: 200, height: 260, borderRadius: 20, overflow: 'hidden',
    backgroundColor: C.surfaceLowest,
    shadowColor: '#000', shadowOpacity: 0.1, shadowRadius: 12, shadowOffset: { width: 0, height: 4 }, elevation: 3,
  },
  trendCardImage: { width: '100%', height: '100%', position: 'absolute' },
  trendCardOverlay: { ...StyleSheet.absoluteFillObject, backgroundColor: 'rgba(0,0,0,0.5)' },
  trendCardContent: { position: 'absolute', bottom: 0, left: 0, right: 0, padding: 16 },
  trendCardTitle: { fontSize: 16, fontWeight: '800', color: '#fff', marginBottom: 6 },
  trendCardMeta: { flexDirection: 'row', alignItems: 'center', gap: 4 },
  trendCardMetaText: { fontSize: 11, color: 'rgba(255,255,255,0.8)', fontWeight: '500' },

  aiBanner: {
    backgroundColor: C.primary, borderRadius: 24, padding: 24,
    overflow: 'hidden', position: 'relative', minHeight: 160, justifyContent: 'center', marginBottom: 40,
  },
  aiBannerBg: { position: 'absolute', right: -40, bottom: -40, zIndex: 0 },
  aiBannerIcon: { opacity: 0.8 },
  aiBannerContent: { zIndex: 1, alignItems: 'flex-start', maxWidth: '75%' },
  aiBannerTitle: { fontSize: 20, fontWeight: 'bold', color: C.onPrimary, marginBottom: 8 },
  aiBannerSub: { fontSize: 13, color: 'rgba(209,255,200,0.8)', lineHeight: 20, marginBottom: 16 },
  aiBannerBtn: { backgroundColor: C.onPrimary, paddingHorizontal: 20, paddingVertical: 10, borderRadius: 20 },
  aiBannerBtnText: { color: C.primary, fontSize: 14, fontWeight: 'bold' },
});
