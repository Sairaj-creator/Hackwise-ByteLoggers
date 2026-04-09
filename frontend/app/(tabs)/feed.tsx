import React, { useEffect, useState, useCallback } from 'react';
import { View, Text, StyleSheet, TouchableOpacity, FlatList, RefreshControl, Image, ActivityIndicator } from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { useRouter } from 'expo-router';
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
  outlineVariant: '#acadad',
};

export default function FeedScreen() {
  const insets = useSafeAreaInsets();
  const router = useRouter();
  const [ingredients, setIngredients] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  const loadFeed = useCallback(async () => {
    try {
      const data = await api.getIngredientsFeed();
      setIngredients(data.ingredients || []);
    } catch (e) {
      console.log('Failed to fetch ingredients feed', e);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { loadFeed(); }, [loadFeed]);
  const onRefresh = async () => { setRefreshing(true); await loadFeed(); setRefreshing(false); };

  const renderCard = ({ item, index }: { item: any; index: number }) => (
    <View style={styles.card}>
      <Image
        source={{ uri: PLACEHOLDER_IMAGES[index % PLACEHOLDER_IMAGES.length] }}
        style={styles.cardImage}
      />
      <View style={styles.cardOverlay} />

      <View style={styles.caloriesBadge}>
        <Ionicons name="flame" size={16} color={C.secondary} />
        <Text style={styles.caloriesText}>{item.calories_per_100g} kcal</Text>
      </View>

      <View style={styles.cardContent}>
        <Text style={styles.cardTitle}>{item.name}</Text>
        
        {/* Macros */}
        <View style={styles.macrosRow}>
          <View style={styles.macroBadge}>
            <Text style={styles.macroValue}>{item.protein_g}g</Text>
            <Text style={styles.macroLabel}>Protein</Text>
          </View>
          <View style={styles.macroBadge}>
            <Text style={styles.macroValue}>{item.carbs_g}g</Text>
            <Text style={styles.macroLabel}>Carbs</Text>
          </View>
          <View style={styles.macroBadge}>
            <Text style={styles.macroValue}>{item.fats_g}g</Text>
            <Text style={styles.macroLabel}>Fats</Text>
          </View>
        </View>

        {/* Benefits */}
        <View style={styles.benefitsContainer}>
          {(item.benefits || []).map((benefit: string, idx: number) => (
            <View key={idx} style={styles.benefitRow}>
              <Ionicons name="checkmark-circle" size={16} color={C.primary} />
              <Text style={styles.benefitText}>{benefit}</Text>
            </View>
          ))}
        </View>
      </View>
    </View>
  );

  return (
    <View style={[styles.container, { paddingTop: insets.top }]}>
      <View style={styles.appBar}>
        <Text style={styles.appBarTitle}>Ingredia</Text>
        <TouchableOpacity style={styles.iconBtn}>
          <Ionicons name="filter" size={24} color={C.onSurfaceVariant} />
        </TouchableOpacity>
      </View>

      <View style={styles.sectionHeader}>
        <Text style={styles.sectionLabel}>NUTRITION INTELLIGENCE</Text>
        <Text style={styles.sectionTitle}>Ingredients Feed</Text>
        <Text style={styles.sectionSub}>Explore the health benefits and exact nutritional value of superfoods around you.</Text>
        <TouchableOpacity style={styles.guideBtn} onPress={() => router.push('/ingredient-benefits')}>
          <Ionicons name="leaf" size={14} color={C.primary} />
          <Text style={styles.guideBtnText}>View Ingredient Guide</Text>
          <Ionicons name="arrow-forward" size={14} color={C.primary} />
        </TouchableOpacity>
      </View>

      {loading ? (
        <View style={styles.loadingContainer}>
          <ActivityIndicator size="large" color={C.primary} />
          <Text style={styles.loadingText}>Loading superfood data from AI...</Text>
        </View>
      ) : ingredients.length === 0 ? (
        <View style={styles.emptyContainer}>
          <Ionicons name="leaf-outline" size={48} color={C.outlineVariant} />
          <Text style={styles.emptyTitle}>No data yet</Text>
          <Text style={styles.emptySub}>Pull down to refresh and load the latest superfood insights.</Text>
        </View>
      ) : (
        <FlatList
          data={ingredients}
          keyExtractor={(item, index) => item.id || `feed-item-${index}`}
          contentContainerStyle={styles.list}
          refreshControl={<RefreshControl refreshing={refreshing} onRefresh={onRefresh} tintColor={C.primary} />}
          renderItem={renderCard}
          showsVerticalScrollIndicator={false}
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
  appBarTitle: { fontSize: 20, fontWeight: 'bold', fontStyle: 'italic', color: C.primary, letterSpacing: -0.5 },
  iconBtn: { padding: 4 },
  sectionHeader: { paddingHorizontal: 24, marginBottom: 24 },
  sectionLabel: { fontSize: 12, fontWeight: '700', color: C.secondary, letterSpacing: 1.5, marginBottom: 4 },
  sectionTitle: { fontSize: 28, fontWeight: '900', color: C.onSurface, marginBottom: 8 },
  sectionSub: { fontSize: 14, color: C.onSurfaceVariant, lineHeight: 22 },
  list: { paddingHorizontal: 24, paddingBottom: 100 },
  
  card: {
    borderRadius: 24, overflow: 'hidden', marginBottom: 24,
    backgroundColor: '#fff', elevation: 4, shadowColor: '#000', shadowOpacity: 0.1, shadowRadius: 16, shadowOffset: { width: 0, height: 8 }
  },
  cardImage: { width: '100%', height: 200 },
  cardOverlay: { ...StyleSheet.absoluteFillObject, backgroundColor: 'rgba(0,0,0,0.4)', height: 200 },
  
  caloriesBadge: {
    position: 'absolute', top: 16, right: 16,
    backgroundColor: '#fff', paddingHorizontal: 12, paddingVertical: 6, borderRadius: 20,
    flexDirection: 'row', alignItems: 'center', gap: 6,
    elevation: 4
  },
  caloriesText: { fontWeight: 'bold', fontSize: 14, color: C.onSurface },
  
  cardContent: { padding: 24, backgroundColor: '#fff', borderTopLeftRadius: 24, borderTopRightRadius: 24, marginTop: -24 },
  cardTitle: { fontSize: 24, fontWeight: '900', color: C.onSurface, marginBottom: 16 },
  
  macrosRow: { flexDirection: 'row', justifyContent: 'space-between', marginBottom: 20, backgroundColor: C.surface, borderRadius: 16, padding: 16 },
  macroBadge: { alignItems: 'center', flex: 1 },
  macroValue: { fontSize: 18, fontWeight: 'bold', color: C.onSurface },
  macroLabel: { fontSize: 12, color: C.onSurfaceVariant, fontWeight: '600', marginTop: 4 },
  
  benefitsContainer: { gap: 12 },
  benefitRow: { flexDirection: 'row', alignItems: 'center', gap: 12 },
  benefitText: { fontSize: 15, color: C.onSurfaceVariant, flex: 1, lineHeight: 22, fontWeight: '500' },
  guideBtn: {
    flexDirection: 'row', alignItems: 'center', gap: 6, alignSelf: 'flex-start',
    backgroundColor: 'rgba(0,107,27,0.08)', paddingHorizontal: 14, paddingVertical: 8,
    borderRadius: 20, marginTop: 12,
  },
  guideBtnText: { fontSize: 13, fontWeight: '700', color: C.primary },
  loadingContainer: { flex: 1, alignItems: 'center', justifyContent: 'center', gap: 12 },
  loadingText: { fontSize: 14, color: C.onSurfaceVariant },
  emptyContainer: { flex: 1, alignItems: 'center', justifyContent: 'center', gap: 12, paddingHorizontal: 40 },
  emptyTitle: { fontSize: 18, fontWeight: 'bold', color: C.onSurface },
  emptySub: { fontSize: 13, color: C.onSurfaceVariant, textAlign: 'center', lineHeight: 20 },
});
