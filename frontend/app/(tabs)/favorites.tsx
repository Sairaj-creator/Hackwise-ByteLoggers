import React, { useEffect, useState, useCallback } from 'react';
import { View, Text, StyleSheet, TouchableOpacity, FlatList, RefreshControl, Image } from 'react-native';
import { useRouter } from 'expo-router';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { api } from '@/services/api';
import { Colors, Spacing, Radius, PLACEHOLDER_IMAGES } from '@/constants/theme';
import { Ionicons } from '@expo/vector-icons';

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

  return (
    <View style={[styles.container, { paddingTop: insets.top }]}>
      <Text style={styles.title}>Favorites</Text>
      <FlatList
        data={recipes}
        keyExtractor={(item) => item.recipe_id}
        contentContainerStyle={styles.list}
        refreshControl={<RefreshControl refreshing={refreshing} onRefresh={onRefresh} tintColor={Colors.orange} />}
        renderItem={({ item, index }) => (
          <TouchableOpacity testID={`fav-recipe-${index}`} style={styles.card} onPress={() => router.push(`/recipe/${item.recipe_id}`)}>
            <Image source={{ uri: PLACEHOLDER_IMAGES[index % PLACEHOLDER_IMAGES.length] }} style={styles.cardImage} />
            <View style={styles.cardContent}>
              <Text style={styles.cardTitle} numberOfLines={2}>{item.title}</Text>
              <Text style={styles.cardMeta} numberOfLines={1}>{item.cuisine} · {item.total_time_minutes || item.cook_time_minutes} min · {item.difficulty}</Text>
              <View style={styles.tagRow}>
                {(item.tags || []).slice(0, 3).map((tag: string) => (
                  <View key={tag} style={styles.tag}><Text style={styles.tagText}>{tag}</Text></View>
                ))}
              </View>
            </View>
            <Ionicons name="heart" size={22} color={Colors.critical} style={{ marginRight: 8 }} />
          </TouchableOpacity>
        )}
        ListEmptyComponent={
          <View style={styles.empty}>
            <Ionicons name="heart-outline" size={64} color={Colors.expired} />
            <Text style={styles.emptyTitle}>No favorites yet</Text>
            <Text style={styles.emptyText}>Recipes you favorite will appear here</Text>
          </View>
        }
      />
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: Colors.bg },
  title: { fontSize: 28, fontWeight: '900', color: Colors.textPrimary, paddingHorizontal: Spacing.lg, paddingVertical: Spacing.md },
  list: { paddingHorizontal: Spacing.lg, paddingBottom: Spacing.xxl },
  card: { flexDirection: 'row', alignItems: 'center', backgroundColor: Colors.card, borderRadius: Radius.xl, overflow: 'hidden', marginBottom: Spacing.sm, borderWidth: 1, borderColor: Colors.borderSubtle },
  cardImage: { width: 80, height: 80 },
  cardContent: { flex: 1, padding: Spacing.md },
  cardTitle: { fontSize: 16, fontWeight: '700', color: Colors.textPrimary },
  cardMeta: { fontSize: 12, color: Colors.textSecondary, marginTop: 4 },
  tagRow: { flexDirection: 'row', gap: 4, marginTop: 6 },
  tag: { backgroundColor: Colors.inputBg, paddingHorizontal: 8, paddingVertical: 3, borderRadius: Radius.full },
  tagText: { fontSize: 11, color: Colors.textSecondary, fontWeight: '600' },
  empty: { alignItems: 'center', paddingTop: 100 },
  emptyTitle: { fontSize: 18, fontWeight: '700', color: Colors.textPrimary, marginTop: Spacing.md },
  emptyText: { fontSize: 14, color: Colors.textSecondary, marginTop: Spacing.xs },
});
