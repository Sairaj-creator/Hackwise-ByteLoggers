import React, { useEffect, useState, useCallback } from 'react';
import { View, Text, StyleSheet, TouchableOpacity, FlatList, RefreshControl, Image } from 'react-native';
import { useRouter } from 'expo-router';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
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
  surfaceContainerHigh: '#e1e3e3',
  tertiaryContainer: '#c1fd7c',
  onTertiaryContainer: '#396100',
  secondaryContainer: '#ffc791',
  onSecondaryContainer: '#6a3c00',
  primaryContainer: '#91f78e',
  onPrimaryContainer: '#005e17',
  outlineVariant: '#acadad',
  outline: '#767777',
  errorContainer: '#f95630',
};

const DEFAULT_AVATAR = 'https://lh3.googleusercontent.com/aida-public/AB6AXuAShg27lH1Uy0oyaQyZGREeY0SCgowi__hBVe98LnW7FsxeKgI-ydIPwUBzWWkX_olSRNDi8pNyMVHxGtESg6ltLAEMQnk0EfWFvpkooESQRBT5lfD1Q4O5MEQZBx61bzW0yPOSLLHPKLr-VbQe1pgVHPmQIkF4j_eZXqjSo_O2UQJY3NtTNYEb1ZUzjRYGjZAtAogUPhw5PMNb4fRhjgc3Yt0tn7hnBL4uY6DVvdCZLXtGhUGp4iqX12UYcxTYCGXek4lA4ZeemiGT';

export default function FavoritesScreen() {
  const insets = useSafeAreaInsets();
  const router = useRouter();
  const [recipes, setRecipes] = useState<any[]>([]);
  const [refreshing, setRefreshing] = useState(false);

  const loadFavorites = useCallback(async () => {
    try {
      const data = await api.getFavorites();
      setRecipes(data.recipes || []);
    } catch {}
  }, []);

  useEffect(() => { loadFavorites(); }, [loadFavorites]);

  const onRefresh = async () => { setRefreshing(true); await loadFavorites(); setRefreshing(false); };

  const renderCard = ({ item, index }: { item: any; index: number }) => (
    <TouchableOpacity
      testID={`fav-recipe-${index}`}
      style={styles.card}
      onPress={() => router.push(`/recipe/${item.recipe_id}`)}
      activeOpacity={0.8}
    >
      <Image
        source={{ uri: PLACEHOLDER_IMAGES[index % PLACEHOLDER_IMAGES.length] }}
        style={styles.cardImage}
      />
      {/* Gradient overlay */}
      <View style={styles.cardOverlay} />

      {/* Favorite heart badge */}
      <View style={styles.heartBadge}>
        <Ionicons name="heart" size={16} color={C.errorContainer} />
      </View>

      {/* Card content */}
      <View style={styles.cardContent}>
        <Text style={styles.cardTitle} numberOfLines={2}>{item.title}</Text>
        <View style={styles.metaRow}>
          <View style={styles.metaItem}>
            <Ionicons name="time-outline" size={12} color="rgba(255,255,255,0.7)" />
            <Text style={styles.metaText}>{item.estimated_time_minutes || item.total_time_minutes || 25} min</Text>
          </View>
          <View style={styles.metaDot} />
          <View style={styles.metaItem}>
            <Ionicons name="flame-outline" size={12} color="rgba(255,255,255,0.7)" />
            <Text style={styles.metaText}>{item.difficulty || 'Easy'}</Text>
          </View>
          {item.cuisine ? (
            <>
              <View style={styles.metaDot} />
              <Text style={styles.metaText}>{item.cuisine}</Text>
            </>
          ) : null}
        </View>
        <View style={styles.tagRow}>
          {(item.tags || []).slice(0, 3).map((tag: string) => (
            <View key={tag} style={styles.tag}>
              <Text style={styles.tagText}>{tag}</Text>
            </View>
          ))}
        </View>
      </View>
    </TouchableOpacity>
  );

  return (
    <View style={[styles.container, { paddingTop: insets.top }]}>
      {/* App bar */}
      <View style={styles.appBar}>
        <View style={styles.appBarLeft}>
          <View style={styles.headerAvatarWrap}>
            <Image source={{ uri: DEFAULT_AVATAR }} style={styles.headerAvatar} />
          </View>
        </View>
        <Text style={styles.appBarTitle}>The Culinary Editorial</Text>
        <TouchableOpacity style={styles.iconBtn}>
          <Ionicons name="search-outline" size={24} color={C.onSurfaceVariant} />
        </TouchableOpacity>
      </View>

      {/* Section header */}
      <View style={styles.sectionHeader}>
        <Text style={styles.sectionLabel}>YOUR SAVED COLLECTION</Text>
        <Text style={styles.sectionTitle}>Favorited Recipes</Text>
        <Text style={styles.sectionSub}>Your personally curated culinary bookmarks, ready to revisit anytime.</Text>
      </View>

      <FlatList
        data={recipes}
        keyExtractor={(item) => item.recipe_id}
        contentContainerStyle={styles.list}
        refreshControl={<RefreshControl refreshing={refreshing} onRefresh={onRefresh} tintColor={C.primary} />}
        renderItem={renderCard}
        showsVerticalScrollIndicator={false}
        ListEmptyComponent={
          <View style={styles.empty}>
            <View style={styles.emptyIconWrap}>
              <Ionicons name="heart-outline" size={48} color={C.outlineVariant} />
            </View>
            <Text style={styles.emptyTitle}>No favorites yet</Text>
            <Text style={styles.emptyText}>Recipes you save from your kitchen will appear here as your personal curated collection.</Text>
            <TouchableOpacity style={styles.emptyBtn} onPress={() => router.push('/(tabs)/home')}>
              <Text style={styles.emptyBtnText}>Explore Recipes</Text>
              <Ionicons name="arrow-forward" size={16} color={C.onPrimary} />
            </TouchableOpacity>
          </View>
        }
      />
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

  sectionHeader: { paddingHorizontal: 24, marginBottom: 24 },
  sectionLabel: { fontSize: 12, fontWeight: '700', color: C.secondary, letterSpacing: 1.5, marginBottom: 4 },
  sectionTitle: { fontSize: 28, fontWeight: '900', color: C.onSurface, marginBottom: 8 },
  sectionSub: { fontSize: 14, color: C.onSurfaceVariant, lineHeight: 22 },

  list: { paddingHorizontal: 24, paddingBottom: 100 },

  card: {
    borderRadius: 24, overflow: 'hidden', marginBottom: 20,
    height: 260, position: 'relative',
    backgroundColor: C.surfaceLow,
    shadowColor: '#2d2f2f', shadowOffset: { width: 0, height: 12 },
    shadowOpacity: 0.06, shadowRadius: 32, elevation: 4,
  },
  cardImage: { width: '100%', height: '100%', position: 'absolute' },
  cardOverlay: {
    ...StyleSheet.absoluteFillObject,
    backgroundColor: 'transparent',
    // Using a simple gradient effect via layered opacity
    borderBottomLeftRadius: 24, borderBottomRightRadius: 24,
    // Overlay for text readability
    // We'll use a gradient-like effect
  },
  heartBadge: {
    position: 'absolute', top: 16, right: 16,
    backgroundColor: 'rgba(255,255,255,0.9)', padding: 8, borderRadius: 16,
    shadowColor: '#000', shadowOpacity: 0.1, shadowRadius: 4, elevation: 2,
  },
  cardContent: {
    position: 'absolute', bottom: 0, left: 0, right: 0,
    padding: 20,
    backgroundColor: 'rgba(0,0,0,0.55)',
  },
  cardTitle: { fontSize: 22, fontWeight: 'bold', color: '#fff', marginBottom: 8 },
  metaRow: { flexDirection: 'row', alignItems: 'center', gap: 8, marginBottom: 12 },
  metaItem: { flexDirection: 'row', alignItems: 'center', gap: 4 },
  metaDot: { width: 3, height: 3, borderRadius: 2, backgroundColor: 'rgba(255,255,255,0.5)' },
  metaText: { fontSize: 12, color: 'rgba(255,255,255,0.8)', fontWeight: '500' },
  tagRow: { flexDirection: 'row', gap: 8, flexWrap: 'wrap' },
  tag: {
    backgroundColor: 'rgba(255,255,255,0.2)', paddingHorizontal: 12, paddingVertical: 5,
    borderRadius: 12, borderWidth: 1, borderColor: 'rgba(255,255,255,0.1)',
  },
  tagText: { fontSize: 11, color: '#fff', fontWeight: '600' },

  empty: { alignItems: 'center', paddingTop: 80, paddingHorizontal: 32 },
  emptyIconWrap: {
    width: 88, height: 88, borderRadius: 44, backgroundColor: C.surfaceLow,
    alignItems: 'center', justifyContent: 'center', marginBottom: 24,
  },
  emptyTitle: { fontSize: 22, fontWeight: '900', color: C.onSurface, marginBottom: 12 },
  emptyText: { fontSize: 14, color: C.onSurfaceVariant, textAlign: 'center', lineHeight: 22, marginBottom: 24 },
  emptyBtn: {
    flexDirection: 'row', alignItems: 'center', gap: 8,
    backgroundColor: C.primary, paddingHorizontal: 24, paddingVertical: 14, borderRadius: 16,
  },
  emptyBtnText: { color: C.onPrimary, fontSize: 14, fontWeight: 'bold' },
});
