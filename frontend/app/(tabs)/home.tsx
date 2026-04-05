import React, { useEffect, useState, useCallback } from 'react';
import { View, Text, StyleSheet, TouchableOpacity, ScrollView, RefreshControl, Image } from 'react-native';
import { useRouter } from 'expo-router';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { useAuth } from '@/context/AuthContext';
import { api } from '@/services/api';
import { PLACEHOLDER_IMAGES } from '@/constants/theme';
import { Ionicons } from '@expo/vector-icons';

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
  const [recipes, setRecipes] = useState<any[]>([]);
  const [trendingRecipes, setTrendingRecipes] = useState<any[]>([]);
  const [location, setLocation] = useState<string>('Detecting location...');
  const [refreshing, setRefreshing] = useState(false);

  const loadData = useCallback(async () => {
    try {
      const loc = await api.getUserLocation();
      setLocation(loc);
      const [fridge, recipeData, trendingData] = await Promise.all([
        api.getFridge(), 
        api.getMyRecipes(),
        api.getTrendingRecipes(loc)
      ]);
      setFridgeData(fridge);
      setRecipes(recipeData.recipes || []);
      setTrendingRecipes(trendingData.recipes || []);
    } catch {}
  }, []);

  useEffect(() => { loadData(); }, [loadData]);

  const onRefresh = async () => { setRefreshing(true); await loadData(); setRefreshing(false); };
  
  const heroRecipe = trendingRecipes.length > 0 ? trendingRecipes[0] : null;
  const recentRecipes = trendingRecipes.length > 1 ? trendingRecipes.slice(1, 5) : [];

  return (
    <View style={[styles.container, { paddingTop: insets.top }]}>
      {/* Header */}
      <View style={styles.header}>
        <TouchableOpacity style={styles.iconBtn} onPress={() => router.push('/(tabs)/profile')}>
          <Ionicons name="menu" size={24} color={C.primary} />
        </TouchableOpacity>
        <Text style={styles.headerTitle}>The Culinary Editorial</Text>
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
          <Text style={styles.welcomeTitle}>{user?.name ? `${user.name}'s\nVerdant AI Kitchen` : 'Verdant AI Kitchen'}</Text>
          <Text style={styles.welcomeSub}>Curated flavors and intelligent pairings, tailored to your available ingredients.</Text>
        </View>

        {/* Featured Section */}
        <View style={styles.sectionHeader}>
          <Text style={styles.editorChoice}>LOCAL TRENDS</Text>
          <Text style={styles.sectionTitle}>Trending in {location}</Text>
        </View>

        {heroRecipe ? (
          <View style={styles.heroCard}>
            <View style={styles.heroImageContainer}>
               <Image source={{ uri: PLACEHOLDER_IMAGES[0 % PLACEHOLDER_IMAGES.length] }} style={styles.heroImage} />
               <View style={styles.aiBadge}>
                  <Ionicons name="flash" size={12} color={C.primary} />
                  <Text style={styles.aiBadgeText}>AI MATCH 98%</Text>
               </View>
            </View>
            <View style={styles.heroContent}>
              <Text style={styles.heroTitle}>{heroRecipe.title}</Text>
              <Text style={styles.heroSub} numberOfLines={2}>A celebration of your local ingredients crafted just for you.</Text>
              <View style={styles.heroMetaRow}>
                <View style={styles.metaBadge}>
                  <Ionicons name="time-outline" size={14} color={C.secondary} />
                  <Text style={styles.metaText}>{heroRecipe.total_time_minutes || 35} MIN</Text>
                </View>
                <View style={styles.metaBadge}>
                  <Ionicons name="flame-outline" size={14} color={C.secondary} />
                  <Text style={styles.metaText}>{heroRecipe.difficulty || 'Easy'}</Text>
                </View>
              </View>
              <TouchableOpacity style={styles.heroBtn} onPress={() => router.push(`/recipe/${heroRecipe.recipe_id}`)}>
                <Text style={styles.heroBtnText}>View Recipe</Text>
                <Ionicons name="arrow-forward" size={16} color={C.onPrimary} />
              </TouchableOpacity>
            </View>
          </View>
        ) : (
          <View style={[styles.heroCard, { padding: 24, alignItems: 'center' }]}>
            <Ionicons name="restaurant-outline" size={48} color={C.outlineVariant} />
            <Text style={[styles.heroTitle, {marginTop: 12}]}>No recipes yet</Text>
            <Text style={[styles.heroSub, {textAlign: 'center', marginBottom: 12}]}>Add items to your fridge and let AI create amazing recipes for you!</Text>
            <TouchableOpacity style={styles.heroBtn} onPress={() => router.push('/(tabs)/fridge')}>
                <Text style={styles.heroBtnText}>Manage Fridge</Text>
            </TouchableOpacity>
          </View>
        )}

        {/* Bento Feed Grid */}
        {recentRecipes.length > 0 && (
          <View style={styles.grid}>
            {recentRecipes.map((recipe, i) => (
              <TouchableOpacity key={recipe.recipe_id} style={styles.gridCard} onPress={() => router.push(`/recipe/${recipe.recipe_id}`)}>
                <View style={styles.gridImageContainer}>
                  <Image source={{ uri: PLACEHOLDER_IMAGES[(i+1) % PLACEHOLDER_IMAGES.length] }} style={styles.gridImage} />
                </View>
                <View style={styles.gridContent}>
                  <View style={styles.gridRow}>
                    <Text style={styles.gridTitle} numberOfLines={1}>{recipe.title}</Text>
                    <Ionicons name="heart-outline" size={18} color={C.onSurfaceVariant} />
                  </View>
                  <Text style={styles.gridSub} numberOfLines={2}>Perfectly paired with your saved ingredients.</Text>
                  <View style={styles.gridTags}>
                    <View style={[styles.gridTag, { backgroundColor: C.secondaryContainer }]}>
                      <Text style={[styles.gridTagText, { color: C.onSecondaryContainer }]}>{recipe.difficulty || 'EASY'}</Text>
                    </View>
                    <View style={[styles.gridTag, { backgroundColor: C.primaryContainer }]}>
                      <Text style={[styles.gridTagText, { color: C.onPrimaryContainer }]}>{recipe.total_time_minutes || 20} MIN</Text>
                    </View>
                  </View>
                </View>
              </TouchableOpacity>
            ))}
          </View>
        )}

        {/* AI Assistant Banner */}
        <View style={styles.aiBanner}>
          <View style={styles.aiBannerBg}>
            <Ionicons name="sparkles" size={160} color="rgba(255,255,255,0.05)" style={styles.aiBannerIcon} />
          </View>
          <View style={styles.aiBannerContent}>
            <Text style={styles.aiBannerTitle}>What's in your fridge?</Text>
            <Text style={styles.aiBannerSub}>Snap a photo and let our AI curate a recipe from your available ingredients.</Text>
            <TouchableOpacity style={styles.aiBannerBtn} onPress={() => router.push('/(tabs)/generate')}>
              <Text style={styles.aiBannerBtnText}>Start Scan</Text>
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
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingHorizontal: 24,
    paddingVertical: 16,
    backgroundColor: C.surface,
  },
  iconBtn: { padding: 4 },
  headerTitle: { fontSize: 20, fontWeight: 'bold', fontStyle: 'italic', color: C.primary },
  avatarBorder: {
    width: 40, height: 40,
    borderRadius: 20,
    borderWidth: 2,
    borderColor: C.primaryContainer,
    overflow: 'hidden',
  },
  avatar: { width: '100%', height: '100%' },
  content: { paddingHorizontal: 24, paddingBottom: 100 },
  welcomeSection: { marginTop: 16, marginBottom: 32 },
  locationRow: { flexDirection: 'row', alignItems: 'center', gap: 4, marginBottom: 8 },
  locationText: { fontSize: 12, fontWeight: '600', color: C.tertiary, letterSpacing: 0.5 },
  welcomeTitle: { fontSize: 36, fontWeight: '900', color: C.onSurface, lineHeight: 42, marginBottom: 8 },
  welcomeSub: { fontSize: 16, color: C.onSurfaceVariant, lineHeight: 24, maxWidth: '90%' },
  sectionHeader: { marginBottom: 24 },
  editorChoice: { fontSize: 12, fontWeight: '700', color: C.secondary, letterSpacing: 1.5, marginBottom: 4 },
  sectionTitle: { fontSize: 24, fontWeight: 'bold', color: C.onSurface },
  heroCard: {
    backgroundColor: C.surfaceLowest,
    borderRadius: 24,
    overflow: 'hidden',
    marginBottom: 32,
    shadowColor: C.onSurface,
    shadowOffset: { width: 0, height: 12 },
    shadowOpacity: 0.06,
    shadowRadius: 32,
    elevation: 4,
  },
  heroImageContainer: { height: 240, width: '100%', position: 'relative' },
  heroImage: { width: '100%', height: '100%' },
  aiBadge: {
    position: 'absolute', top: 16, left: 16,
    backgroundColor: 'rgba(255,255,255,0.9)',
    flexDirection: 'row', alignItems: 'center', gap: 4,
    paddingHorizontal: 10, paddingVertical: 6,
    borderRadius: 16,
  },
  aiBadgeText: { fontSize: 10, fontWeight: '800', color: C.primary },
  heroContent: { padding: 24, gap: 12 },
  heroTitle: { fontSize: 22, fontWeight: 'bold', color: C.onSurface },
  heroSub: { fontSize: 14, color: C.onSurfaceVariant, lineHeight: 20 },
  heroMetaRow: { flexDirection: 'row', gap: 16, paddingVertical: 12, borderTopWidth: 1, borderBottomWidth: 1, borderColor: 'rgba(172,173,173,0.2)' },
  metaBadge: { flexDirection: 'row', alignItems: 'center', gap: 6 },
  metaText: { fontSize: 12, fontWeight: '600', color: C.onSurface },
  heroBtn: {
    backgroundColor: C.primary,
    flexDirection: 'row', alignItems: 'center', justifyContent: 'center', gap: 8,
    paddingVertical: 16, borderRadius: 12, marginTop: 8,
  },
  heroBtnText: { color: C.onPrimary, fontSize: 16, fontWeight: 'bold' },
  grid: { flexDirection: 'row', flexWrap: 'wrap', justifyContent: 'space-between', marginBottom: 32 },
  gridCard: {
    width: '48%',
    backgroundColor: C.surfaceLow,
    borderRadius: 24,
    padding: 16,
    marginBottom: 16,
  },
  gridImageContainer: { width: '100%', aspectRatio: 1, borderRadius: 12, overflow: 'hidden', marginBottom: 12 },
  gridImage: { width: '100%', height: '100%' },
  gridContent: { gap: 8 },
  gridRow: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'flex-start' },
  gridTitle: { fontSize: 16, fontWeight: 'bold', color: C.onSurface, flex: 1, marginRight: 8 },
  gridSub: { fontSize: 12, color: C.onSurfaceVariant, fontWeight: '500' },
  gridTags: { flexDirection: 'row', flexWrap: 'wrap', gap: 8, marginTop: 4 },
  gridTag: { paddingHorizontal: 8, paddingVertical: 4, borderRadius: 4 },
  gridTagText: { fontSize: 10, fontWeight: 'bold', textTransform: 'uppercase' },
  aiBanner: {
    backgroundColor: C.primary,
    borderRadius: 24,
    padding: 24,
    overflow: 'hidden',
    position: 'relative',
    minHeight: 180,
    justifyContent: 'center',
    marginBottom: 40,
  },
  aiBannerBg: { position: 'absolute', right: -40, bottom: -40, zIndex: 0 },
  aiBannerIcon: { opacity: 0.8 },
  aiBannerContent: { zIndex: 1, alignItems: 'flex-start', maxWidth: '75%' },
  aiBannerTitle: { fontSize: 20, fontWeight: 'bold', color: C.onPrimary, marginBottom: 8 },
  aiBannerSub: { fontSize: 14, color: 'rgba(209,255,200,0.8)', lineHeight: 20, marginBottom: 16 },
  aiBannerBtn: { backgroundColor: C.onPrimary, paddingHorizontal: 20, paddingVertical: 10, borderRadius: 20 },
  aiBannerBtnText: { color: C.primary, fontSize: 14, fontWeight: 'bold' }
});
