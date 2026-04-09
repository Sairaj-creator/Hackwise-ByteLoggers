import React, { useEffect, useState, useCallback } from 'react';
import {
  View, Text, StyleSheet, FlatList, TouchableOpacity,
  Image, RefreshControl, ActivityIndicator, ScrollView,
} from 'react-native';
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
  primaryContainer: '#91f78e',
  onPrimaryContainer: '#005e17',
  secondaryContainer: '#ffc791',
  onSecondaryContainer: '#6a3c00',
  tertiaryContainer: '#c1fd7c',
  onTertiaryContainer: '#396100',
  surfaceLowest: '#ffffff',
  surfaceLow: '#f0f1f1',
  outlineVariant: '#acadad',
};

export default function FavoritesScreen() {
  const insets = useSafeAreaInsets();
  const router = useRouter();
  const [favorites, setFavorites] = useState<any[]>([]);
  const [feedPosts, setFeedPosts] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [likedPosts, setLikedPosts] = useState<Set<string>>(new Set());

  const loadData = useCallback(async () => {
    try {
      const [favData, feedData] = await Promise.allSettled([
        api.getFavorites(),
        api.getSocialFeed(1),
      ]);
      if (favData.status === 'fulfilled') setFavorites(favData.value.recipes || []);
      if (feedData.status === 'fulfilled') setFeedPosts(feedData.value.posts || []);
    } catch (e) {
      console.log('Failed to load favorites/feed', e);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { loadData(); }, [loadData]);

  const onRefresh = async () => {
    setRefreshing(true);
    await loadData();
    setRefreshing(false);
  };

  const handleToggleLike = async (postId: string) => {
    try {
      await api.toggleLike(postId);
      setLikedPosts(prev => {
        const next = new Set(prev);
        next.has(postId) ? next.delete(postId) : next.add(postId);
        return next;
      });
    } catch {}
  };

  if (loading) {
    return (
      <View style={[styles.container, { paddingTop: insets.top, justifyContent: 'center', alignItems: 'center' }]}>
        <ActivityIndicator size="large" color={C.primary} />
      </View>
    );
  }

  return (
    <ScrollView
      style={[styles.container, { paddingTop: insets.top }]}
      contentContainerStyle={styles.scrollContent}
      showsVerticalScrollIndicator={false}
      refreshControl={<RefreshControl refreshing={refreshing} onRefresh={onRefresh} tintColor={C.primary} />}
    >
      {/* App Bar */}
      <View style={styles.appBar}>
        <Text style={styles.appBarTitle}>Ingredia</Text>
        <TouchableOpacity style={styles.iconBtn} onPress={() => router.push('/(tabs)/generate')}>
          <Ionicons name="add-circle-outline" size={26} color={C.primary} />
        </TouchableOpacity>
      </View>

      {/* ─── SAVED RECIPES SECTION ─── */}
      <View style={styles.sectionHeader}>
        <Text style={styles.sectionLabel}>YOUR COLLECTION</Text>
        <Text style={styles.sectionTitle}>Saved Recipes</Text>
        <Text style={styles.sectionSub}>Your curated library of AI-generated favorites.</Text>
      </View>

      {favorites.length === 0 ? (
        <View style={styles.emptyCard}>
          <Ionicons name="heart-outline" size={40} color={C.outlineVariant} />
          <Text style={styles.emptyTitle}>No favorites yet</Text>
          <Text style={styles.emptySub}>Tap the heart on any recipe to save it here.</Text>
          <TouchableOpacity style={styles.emptyBtn} onPress={() => router.push('/(tabs)/generate')}>
            <Text style={styles.emptyBtnText}>Generate a Recipe</Text>
          </TouchableOpacity>
        </View>
      ) : (
        <ScrollView
          horizontal
          showsHorizontalScrollIndicator={false}
          contentContainerStyle={styles.favRow}
        >
          {favorites.map((item, index) => (
            <TouchableOpacity
              key={item.recipe_id || index}
              style={styles.favCard}
              onPress={() => router.push(`/recipe/${item.recipe_id}`)}
              activeOpacity={0.85}
            >
              <Image
                source={{ uri: item.image_url || PLACEHOLDER_IMAGES[index % PLACEHOLDER_IMAGES.length] }}
                style={styles.favCardImage}
              />
              <View style={styles.favCardOverlay} />
              <View style={styles.favCardContent}>
                <View style={styles.favBadge}>
                  <Ionicons name="heart" size={10} color={C.primary} />
                  <Text style={styles.favBadgeText}>SAVED</Text>
                </View>
                <Text style={styles.favCardTitle} numberOfLines={2}>{item.title}</Text>
                <Text style={styles.favCardMeta}>{item.cuisine} · {item.estimated_time_minutes || 30} min</Text>
              </View>
            </TouchableOpacity>
          ))}
        </ScrollView>
      )}

      {/* ─── COMMUNITY FEED SECTION ─── */}
      <View style={[styles.sectionHeader, { marginTop: 40 }]}>
        <Text style={styles.sectionLabel}>COMMUNITY</Text>
        <Text style={styles.sectionTitle}>Recipe Feed</Text>
        <Text style={styles.sectionSub}>Discover what other chefs are creating with AI.</Text>
      </View>

      {feedPosts.length === 0 ? (
        <View style={styles.emptyCard}>
          <Ionicons name="people-outline" size={40} color={C.outlineVariant} />
          <Text style={styles.emptyTitle}>No posts yet</Text>
          <Text style={styles.emptySub}>The community feed is getting warmed up. Check back soon!</Text>
        </View>
      ) : (
        feedPosts.map((post, index) => {
          const postId = post.id || `post-${index}`;
          const liked = likedPosts.has(postId);
          const userName = post.user?.name || 'Chef';
          return (
            <View key={postId} style={styles.postCard}>
              {post.image_url ? (
                <Image source={{ uri: post.image_url }} style={styles.postImage} />
              ) : (
                <Image
                  source={{ uri: PLACEHOLDER_IMAGES[index % PLACEHOLDER_IMAGES.length] }}
                  style={styles.postImage}
                />
              )}
              <View style={styles.postContent}>
                <View style={styles.postHeader}>
                  <View style={styles.postAvatar}>
                    <Ionicons name="person" size={16} color={C.primary} />
                  </View>
                  <View style={styles.postMeta}>
                    <Text style={styles.postUserName}>{userName}</Text>
                    <Text style={styles.postTime}>
                      {post.created_at ? new Date(post.created_at).toLocaleDateString('en-IN', { day: 'numeric', month: 'short' }) : ''}
                    </Text>
                  </View>
                </View>
                {post.content ? (
                  <Text style={styles.postText} numberOfLines={3}>{post.content}</Text>
                ) : null}
                {post.recipe_title ? (
                  <View style={styles.recipeTag}>
                    <Ionicons name="restaurant-outline" size={12} color={C.primary} />
                    <Text style={styles.recipeTagText} numberOfLines={1}>{post.recipe_title}</Text>
                  </View>
                ) : null}
                <View style={styles.postActions}>
                  <TouchableOpacity style={styles.postActionBtn} onPress={() => handleToggleLike(postId)}>
                    <Ionicons name={liked ? 'heart' : 'heart-outline'} size={20} color={liked ? C.primary : C.onSurfaceVariant} />
                    <Text style={[styles.postActionText, liked && { color: C.primary }]}>
                      {(post.likes_count || 0) + (liked ? 1 : 0)}
                    </Text>
                  </TouchableOpacity>
                  <View style={styles.postActionBtn}>
                    <Ionicons name="chatbubble-outline" size={18} color={C.onSurfaceVariant} />
                    <Text style={styles.postActionText}>{post.comments_count || 0}</Text>
                  </View>
                </View>
              </View>
            </View>
          );
        })
      )}

      <View style={{ height: 100 }} />
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: C.surface },
  scrollContent: { paddingBottom: 40 },
  appBar: {
    flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center',
    paddingHorizontal: 24, paddingVertical: 16,
  },
  appBarTitle: { fontSize: 20, fontWeight: 'bold', fontStyle: 'italic', color: C.primary, letterSpacing: -0.5 },
  iconBtn: { padding: 4 },

  sectionHeader: { paddingHorizontal: 24, marginBottom: 20 },
  sectionLabel: { fontSize: 12, fontWeight: '700', color: C.secondary, letterSpacing: 1.5, marginBottom: 4 },
  sectionTitle: { fontSize: 28, fontWeight: '900', color: C.onSurface, marginBottom: 8 },
  sectionSub: { fontSize: 14, color: C.onSurfaceVariant, lineHeight: 22 },

  emptyCard: {
    marginHorizontal: 24, backgroundColor: C.surfaceLowest, borderRadius: 24,
    padding: 32, alignItems: 'center', gap: 10,
    borderWidth: 2, borderStyle: 'dashed', borderColor: C.outlineVariant,
  },
  emptyTitle: { fontSize: 18, fontWeight: 'bold', color: C.onSurface },
  emptySub: { fontSize: 13, color: C.onSurfaceVariant, textAlign: 'center', lineHeight: 20 },
  emptyBtn: { backgroundColor: C.primary, paddingHorizontal: 20, paddingVertical: 12, borderRadius: 12, marginTop: 8 },
  emptyBtnText: { color: C.onPrimary, fontSize: 14, fontWeight: 'bold' },

  // Favorites horizontal scroll
  favRow: { paddingHorizontal: 24, paddingBottom: 8, gap: 16 },
  favCard: {
    width: 220, height: 280, borderRadius: 20, overflow: 'hidden',
    backgroundColor: C.surfaceLowest,
    shadowColor: '#000', shadowOpacity: 0.1, shadowRadius: 12, shadowOffset: { width: 0, height: 4 }, elevation: 3,
  },
  favCardImage: { width: '100%', height: '100%', position: 'absolute' },
  favCardOverlay: { ...StyleSheet.absoluteFillObject, backgroundColor: 'rgba(0,0,0,0.45)' },
  favCardContent: { position: 'absolute', bottom: 0, left: 0, right: 0, padding: 20 },
  favBadge: {
    flexDirection: 'row', alignItems: 'center', gap: 4,
    backgroundColor: C.primaryContainer, alignSelf: 'flex-start',
    paddingHorizontal: 8, paddingVertical: 4, borderRadius: 10, marginBottom: 8,
  },
  favBadgeText: { fontSize: 9, fontWeight: '800', color: C.onPrimaryContainer, letterSpacing: 1 },
  favCardTitle: { fontSize: 18, fontWeight: '900', color: '#fff', marginBottom: 4 },
  favCardMeta: { fontSize: 12, color: 'rgba(255,255,255,0.75)', fontWeight: '500' },

  // Community feed posts
  postCard: {
    marginHorizontal: 24, backgroundColor: C.surfaceLowest, borderRadius: 24,
    overflow: 'hidden', marginBottom: 20,
    shadowColor: '#000', shadowOpacity: 0.06, shadowRadius: 12, shadowOffset: { width: 0, height: 4 }, elevation: 2,
  },
  postImage: { width: '100%', height: 200 },
  postContent: { padding: 20 },
  postHeader: { flexDirection: 'row', alignItems: 'center', marginBottom: 12, gap: 12 },
  postAvatar: {
    width: 36, height: 36, borderRadius: 18,
    backgroundColor: C.primaryContainer, alignItems: 'center', justifyContent: 'center',
  },
  postMeta: { flex: 1 },
  postUserName: { fontSize: 14, fontWeight: '700', color: C.onSurface },
  postTime: { fontSize: 11, color: C.onSurfaceVariant, marginTop: 1 },
  postText: { fontSize: 14, color: C.onSurfaceVariant, lineHeight: 22, marginBottom: 16 },
  recipeTag: {
    flexDirection: 'row', alignItems: 'center', gap: 6,
    backgroundColor: 'rgba(0,107,27,0.07)', paddingHorizontal: 10, paddingVertical: 5,
    borderRadius: 10, alignSelf: 'flex-start', marginBottom: 12,
  },
  recipeTagText: { fontSize: 12, fontWeight: '600', color: C.primary, maxWidth: 220 },
  postActions: { flexDirection: 'row', gap: 20, borderTopWidth: 1, borderTopColor: 'rgba(172,173,173,0.15)', paddingTop: 12 },
  postActionBtn: { flexDirection: 'row', alignItems: 'center', gap: 6 },
  postActionText: { fontSize: 13, fontWeight: '600', color: C.onSurfaceVariant },
});
