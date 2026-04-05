import React, { useEffect, useState, useCallback } from 'react';
import { View, Text, StyleSheet, FlatList, Image, TouchableOpacity, RefreshControl, ActivityIndicator } from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { Ionicons } from '@expo/vector-icons';
import { api } from '@/services/api';
import { PLACEHOLDER_IMAGES } from '@/constants/theme';
import { useRouter } from 'expo-router';

const C = {
  surface: '#f6f6f6',
  onSurface: '#2d2f2f',
  onSurfaceVariant: '#5a5c5c',
  primary: '#006b1b',
  primaryDim: '#005d16',
  onPrimary: '#d1ffc8',
  secondaryContainer: '#ffc791',
  surfaceContainerLow: '#f0f1f1',
  surfaceContainerLowest: '#ffffff',
  surfaceContainerHigh: '#e1e3e3',
  tertiaryContainer: '#c1fd7c',
  onTertiaryContainer: '#396100',
  outlineVariant: '#acadad',
  error: '#b02500',
  criticalBg: '#ffefec',
  critical: '#b02500'
};

export default function FeedScreen() {
  const insets = useSafeAreaInsets();
  const router = useRouter();
  const [posts, setPosts] = useState<any[]>([]);
  const [refreshing, setRefreshing] = useState(false);
  const [loading, setLoading] = useState(true);

  const loadFeed = useCallback(async () => {
    try {
        const data = await api.getSocialFeed();
        setPosts(data.posts || []);
    } catch(e) {
        // Silently handle error or show a toast
    } finally {
        setLoading(false);
    }
  }, []);

  useEffect(() => { loadFeed(); }, [loadFeed]);

  const onRefresh = async () => {
      setRefreshing(true);
      await loadFeed();
      setRefreshing(false);
  };

  const renderCard = ({ item, index }: { item: any, index: number }) => {
      const stableIndex = (item.id || String(index)).charCodeAt(0) + index;
      const imageUrl = item.image_url || PLACEHOLDER_IMAGES[stableIndex % PLACEHOLDER_IMAGES.length];
      
      return (
        <TouchableOpacity 
          style={styles.card} 
          activeOpacity={0.9} 
          onPress={() => {
            if (item.recipe_id) router.push(`/recipe/${item.recipe_id}`);
          }}
        >
          <Image source={{ uri: imageUrl }} style={styles.cardImage} />
          <View style={styles.cardOverlay}>
            <View style={styles.badgeRow}>
              {item.recipe_title ? (
                  <View style={styles.badge}>
                    <Text style={styles.badgeText}>COMMUNITY RECIPE</Text>
                  </View>
              ) : (
                  <View style={[styles.badge, { backgroundColor: C.secondaryContainer }]}>
                    <Text style={[styles.badgeText, { color: '#000' }]}>DISCUSSION</Text>
                  </View>
              )}
            </View>
            <Text style={styles.cardTitle}>{item.recipe_title || `${item.user?.name || 'Chef'}'s Post`}</Text>
            {item.content ? (
                <Text style={styles.cardDesc} numberOfLines={2}>{item.content}</Text>
            ) : null}
            
            <View style={styles.metaRow}>
                <View style={styles.authorRow}>
                    <Ionicons name="person-circle" size={20} color="rgba(255,255,255,0.8)" />
                    <Text style={styles.authorText}>{item.user?.name || 'Unknown'}</Text>
                </View>
                <View style={styles.statsRow}>
                    <View style={styles.stat}>
                        <Ionicons name={item.is_liked ? "heart" : "heart-outline"} size={16} color={item.is_liked ? C.error : '#ffffff'} />
                        <Text style={styles.metaText}>{item.likes_count || 0}</Text>
                    </View>
                    <View style={styles.stat}>
                        <Ionicons name="chatbubble-outline" size={16} color="#ffffff" />
                        <Text style={styles.metaText}>{item.comments_count || 0}</Text>
                    </View>
                </View>
            </View>
          </View>
        </TouchableOpacity>
      );
  };

  const headerComponent = () => (
    <View style={styles.headerBox}>
      <Text style={styles.dailyWisdom}>THE CUTTING BOARD</Text>
      <Text style={styles.title}>Community Creations & Intelligence</Text>
      <Text style={styles.subtitle}>Discover what others are generating in their Verdant Kitchens. Get inspired by community recipes and ingredient hacks.</Text>
    </View>
  );

  return (
    <View style={[styles.container, { paddingTop: insets.top }]}>
      <View style={styles.appBar}>
        <TouchableOpacity style={styles.iconBtn}>
          <Ionicons name="menu-outline" size={24} color={C.primary} />
        </TouchableOpacity>
        <Text style={styles.appBarBrand}>The Culinary Editorial</Text>
        <TouchableOpacity onPress={() => router.push('/(tabs)/profile')} style={styles.avatarBorder}>
          <Image source={{ uri: 'https://lh3.googleusercontent.com/aida-public/AB6AXuC4jSkPRkcV95Ki5NsAW6RsG3TlpVNgLcKKLjbCfUithQKc6yKLtrqXQ7ElaPH_HdWaYJJM9JK0SxDvpyVwtEnNpp37D-A_hj2XDVAFr91y8I_TQ5jRnnFM5WNctNK8N0cLk4dkciBMex3GBxT7RCzYxSopH8YdxX5wV79LiZSIse1oZ63AjGZ6Q3Tm7YTC6FNKOebjZK_RmnkzCFZlyLc8R3kqU7ht8_APzlJ4t_VJwL_CEoQzVXmmXqffu86AszGfcoEMz4eivNhP' }} style={styles.avatar} />
        </TouchableOpacity>
      </View>

      {loading ? (
        <View style={{ flex: 1, justifyContent: 'center', alignItems: 'center' }}>
            <ActivityIndicator size="large" color={C.primary} />
        </View>
      ) : (
        <FlatList 
          data={posts}
          keyExtractor={item => item.id || Math.random().toString()}
          renderItem={renderCard}
          contentContainerStyle={styles.content}
          ListHeaderComponent={headerComponent}
          showsVerticalScrollIndicator={false}
          refreshControl={<RefreshControl refreshing={refreshing} onRefresh={onRefresh} tintColor={C.primary} />}
          ListEmptyComponent={
            <View style={styles.emptyBox}>
                <Ionicons name="nutrition-outline" size={48} color={C.outlineVariant} />
                <Text style={styles.emptyTitle}>Nothing here yet</Text>
                <Text style={styles.emptySub}>The community is warming up their ovens. Check back soon for fresh inspiration.</Text>
            </View>
          }
        />
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: C.surface },
  appBar: {
    flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center',
    paddingHorizontal: 24, paddingVertical: 16, backgroundColor: C.surface,
  },
  iconBtn: { padding: 4 },
  appBarBrand: { fontSize: 18, fontWeight: 'bold', color: C.primary },
  avatarBorder: {
    width: 32, height: 32, borderRadius: 16, overflow: 'hidden', backgroundColor: C.surfaceContainerLow,
    borderWidth: 1, borderColor: 'rgba(0,107,27,0.2)'
  },
  avatar: { width: '100%', height: '100%' },
  
  content: { paddingHorizontal: 24, paddingBottom: 100 },
  headerBox: { marginTop: 8, marginBottom: 32 },
  dailyWisdom: { fontSize: 12, fontWeight: 'bold', letterSpacing: 1, marginBottom: 8, color: '#d18a38' }, 
  title: { fontSize: 32, fontWeight: '900', color: C.onSurface, marginBottom: 12, letterSpacing: -0.5, lineHeight: 38 },
  subtitle: { fontSize: 16, color: C.onSurfaceVariant, lineHeight: 24 },

  card: {
    width: '100%', height: 400, borderRadius: 24, overflow: 'hidden',
    backgroundColor: C.surfaceContainerLow, position: 'relative', marginBottom: 24,
    shadowColor: C.onSurface, shadowOffset: { width: 0, height: 12 }, shadowOpacity: 0.1, shadowRadius: 20, elevation: 6
  },
  cardImage: { width: '100%', height: '100%', position: 'absolute' },
  cardOverlay: {
    ...StyleSheet.absoluteFillObject,
    backgroundColor: 'rgba(0,0,0,0.3)',
    justifyContent: 'flex-end',
    padding: 24
  },
  badgeRow: { flexDirection: 'row', marginBottom: 12 },
  badge: {
    backgroundColor: C.primary, alignSelf: 'flex-start', paddingHorizontal: 12, paddingVertical: 6, borderRadius: 12
  },
  badgeText: { color: C.onPrimary, fontSize: 10, fontWeight: 'bold', letterSpacing: 1 },
  cardTitle: { color: '#ffffff', fontSize: 28, fontWeight: 'bold', marginBottom: 8 },
  cardDesc: { color: 'rgba(255,255,255,0.9)', fontSize: 14, lineHeight: 20 },
  
  metaRow: { 
      flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between',
      marginTop: 16, paddingTop: 16, borderTopWidth: 1, borderTopColor: 'rgba(255,255,255,0.2)'
  },
  authorRow: { flexDirection: 'row', alignItems: 'center', gap: 6 },
  authorText: { color: 'rgba(255,255,255,0.8)', fontSize: 13, fontWeight: '600' },
  statsRow: { flexDirection: 'row', alignItems: 'center', gap: 16 },
  stat: { flexDirection: 'row', alignItems: 'center', gap: 6 },
  metaText: { color: '#ffffff', fontSize: 14, fontWeight: 'bold' },

  emptyBox: { alignItems: 'center', justifyContent: 'center', paddingVertical: 40, gap: 12 },
  emptyTitle: { fontSize: 20, fontWeight: 'bold', color: C.onSurface },
  emptySub: { fontSize: 14, color: C.onSurfaceVariant, textAlign: 'center', maxWidth: '80%', lineHeight: 20 }
});
