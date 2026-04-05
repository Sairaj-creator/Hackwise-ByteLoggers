import React, { useEffect, useState, useCallback } from 'react';
import { View, Text, StyleSheet, TouchableOpacity, FlatList, TextInput, RefreshControl, Alert, Image } from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { useRouter } from 'expo-router';
import { api } from '@/services/api';
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
  error: '#b02500',
};

const CATEGORY_ICONS: Record<string, keyof typeof Ionicons.glyphMap> = {
  'Protein': 'fish',
  'Fats': 'leaf',
  'Greens': 'leaf-outline',
  'Dairy': 'wine',
  'Carbs': 'pizza',
  'Acidity': 'hardware-chip',
  'Other': 'restaurant',
};

export default function FridgeScreen() {
  const insets = useSafeAreaInsets();
  const router = useRouter();
  const [items, setItems] = useState<any[]>([]);
  const [refreshing, setRefreshing] = useState(false);
  const [name, setName] = useState('');
  const [adding, setAdding] = useState(false);

  const loadItems = useCallback(async () => {
    try {
      const data = await api.getFridge();
      setItems(data.ingredients || []);
    } catch {}
  }, []);

  useEffect(() => { loadItems(); }, [loadItems]);

  const onRefresh = async () => { setRefreshing(true); await loadItems(); setRefreshing(false); };

  const handleAdd = async () => {
    if (!name.trim()) return;
    setAdding(true);
    try {
      await api.addIngredients([{ name: name.trim(), category: 'Other', quantity: 1, unit: 'pieces' }]);
      setName('');
      await loadItems();
    } catch {} finally { setAdding(false); }
  };

  const handleClearAll = () => {
    Alert.alert('Clear Fridge', 'Remove all items?', [
      { text: 'Cancel', style: 'cancel' },
      { text: 'Clear', style: 'destructive', onPress: async () => { 
          // Assuming api has clear or sequential deletes
          await Promise.all(items.map(i => api.deleteFridgeItem(i.item_id))); 
          loadItems(); 
        } 
      },
    ]);
  };

  const handleDelete = (itemId: string, itemName: string) => {
    Alert.alert('Delete', `Remove ${itemName} from fridge?`, [
      { text: 'Cancel', style: 'cancel' },
      { text: 'Delete', style: 'destructive', onPress: async () => { await api.deleteFridgeItem(itemId); loadItems(); } },
    ]);
  };

  const renderItem = ({ item }: { item: any }) => {
    const iconName = CATEGORY_ICONS[item.category] || 'restaurant';
    return (
      <View testID={`fridge-item-${item.item_id}`} style={styles.itemCard}>
        <View style={styles.itemIconBox}>
          <Ionicons name={iconName as any} size={20} color={C.tertiary} />
        </View>
        <View style={styles.itemInfo}>
          <Text style={styles.itemName}>{item.name}</Text>
          <Text style={styles.itemCategory}>{item.category || 'Other'}</Text>
        </View>
        <TouchableOpacity testID={`fridge-delete-${item.item_id}`} onPress={() => handleDelete(item.item_id, item.name)} style={styles.deleteBtn}>
          <Ionicons name="close" size={20} color={C.outlineVariant} />
        </TouchableOpacity>
      </View>
    );
  };

  return (
    <View style={[styles.container, { paddingTop: insets.top }]}>
      <View style={styles.appBar}>
        <TouchableOpacity style={styles.iconBtn} onPress={() => router.push('/(tabs)/profile')}>
          <Ionicons name="menu" size={24} color={C.primary} />
        </TouchableOpacity>
        <Text style={styles.appBarTitle}>The Culinary Editorial</Text>
        <TouchableOpacity onPress={() => router.push('/(tabs)/profile')} style={styles.avatarBorder}>
          <Image source={{ uri: 'https://lh3.googleusercontent.com/aida-public/AB6AXuBMn-7UTbtA9AV_trb3iqPgg9s8LUPc-QALMijIWZveNhkriknrphL6eSw7S7OWkBmmNSZ8WCe1B66r2K3coBmKn8fGaKCQe9EewwryLjcPMc2tOMm24uWA4ADTtnyR9Olm8JumcjjyZ4FBFrow0wHKDLefDuEeqzK5PGGv-RtzhDWRfyYNQZ_HWd0FRQdZ2Vbo1X7Z2b6gOkP1EBcJqyBsx1SbR5pDWR2S38Q_ruuimqRsYJgFjC5Rhszc7_P9rqO8uRvkdxLlJEXU' }} style={styles.avatar} />
        </TouchableOpacity>
      </View>

      <FlatList
        data={items}
        keyExtractor={(item) => item.item_id}
        renderItem={renderItem}
        ListHeaderComponent={
          <View style={styles.contentPad}>
            <View style={styles.heroSection}>
              <Text style={styles.heroTitle}>My Digital Fridge</Text>
              <Text style={styles.heroSub}>Catalog your ingredients. Let AI curate your next gourmet masterpiece based on what's available.</Text>
            </View>

            <View style={styles.addSection}>
              <Text style={styles.addLabel}>NEW INGREDIENT</Text>
              <View style={styles.addRow}>
                <View style={styles.inputWrapper}>
                  <TextInput 
                    testID="fridge-name-input"
                    style={styles.input} 
                    placeholder="e.g., Organic Kale..." 
                    placeholderTextColor="rgba(172,173,173,0.5)"
                    value={name}
                    onChangeText={setName}
                  />
                  <Ionicons name="restaurant" size={20} color={C.primary} style={styles.inputIcon} />
                </View>
                <TouchableOpacity testID="fridge-add-btn" style={styles.addBtn} onPress={handleAdd} disabled={adding}>
                  <Text style={styles.addBtnText}>{adding ? '...' : 'ADD'}</Text>
                </TouchableOpacity>
              </View>
            </View>

            <View style={styles.bentoLeft}>
              <View style={styles.statusBox}>
                <View style={styles.statusHeader}>
                  <Ionicons name="cube" size={28} color={C.primary} />
                  <View style={styles.statusBadge}>
                    <Text style={styles.statusBadgeText}>{items.length} ITEMS</Text>
                  </View>
                </View>
                <Text style={styles.statusTitle}>Fridge Status</Text>
                <Text style={styles.statusSub}>Your current inventory is sufficient for multiple potential recipes.</Text>
              </View>
            </View>

            <View style={styles.listHeader}>
              <Text style={styles.listTitle}>Active Inventory</Text>
              {items.length > 0 && (
                <TouchableOpacity onPress={handleClearAll}>
                  <Text style={styles.clearBtnText}>CLEAR ALL</Text>
                </TouchableOpacity>
              )}
            </View>
          </View>
        }
        ListFooterComponent={
          <View style={styles.contentPad}>
              <View style={styles.missingBox}>
                  <Ionicons name="sparkles" size={36} color={C.tertiary} style={{ marginBottom: 12 }} />
                  <Text style={styles.missingTitle}>Missing an essential?</Text>
                  <Text style={styles.missingSub}>Add your staples now to see even more refined recipe suggestions.</Text>
              </View>
          </View>
        }
        contentContainerStyle={styles.listContent}
        refreshControl={<RefreshControl refreshing={refreshing} onRefresh={onRefresh} tintColor={C.primary} />}
      />

      <View style={styles.fabWrapper}>
        <TouchableOpacity style={styles.fab} onPress={() => router.push('/(tabs)/generate')}>
          <Text style={styles.fabText}>GENERATE RECIPES</Text>
          <Ionicons name="chevron-forward" size={18} color={C.onPrimary} style={{fontWeight:'bold'}} />
        </TouchableOpacity>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: C.surface },
  appBar: {
    flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center',
    paddingHorizontal: 24, paddingVertical: 16, backgroundColor: C.surface,
    borderBottomWidth: 1, borderBottomColor: C.surfaceLow,
  },
  iconBtn: { padding: 4 },
  appBarTitle: { fontSize: 20, fontWeight: 'bold', fontStyle: 'italic', color: C.primary },
  avatarBorder: {
    width: 32, height: 32, borderRadius: 16, borderWidth: 1, borderColor: 'rgba(0,107,27,0.2)', overflow: 'hidden',
  },
  avatar: { width: '100%', height: '100%' },
  listContent: { paddingBottom: 160 },
  contentPad: { paddingHorizontal: 24 },
  heroSection: { marginTop: 24, marginBottom: 40 },
  heroTitle: { fontSize: 30, fontWeight: '900', color: C.onSurface, letterSpacing: -0.5, marginBottom: 8 },
  heroSub: { fontSize: 16, color: C.onSurfaceVariant, fontWeight: '500', lineHeight: 24, maxWidth: '90%' },
  addSection: { backgroundColor: C.surfaceLow, borderRadius: 24, padding: 24, marginBottom: 32 },
  addLabel: { fontSize: 14, fontWeight: 'bold', color: C.onSurfaceVariant, letterSpacing: 0.5, marginBottom: 12 },
  addRow: { flexDirection: 'row', gap: 12 },
  inputWrapper: { flex: 1, position: 'relative', justifyContent: 'center' },
  input: {
    backgroundColor: C.surfaceLowest, borderRadius: 12, paddingVertical: 16, paddingLeft: 20, paddingRight: 48,
    fontSize: 16, color: C.onSurface,
  },
  inputIcon: { position: 'absolute', right: 16, opacity: 0.6 },
  addBtn: { backgroundColor: C.secondaryContainer, paddingHorizontal: 32, borderRadius: 12, alignItems: 'center', justifyContent: 'center' },
  addBtnText: { color: C.onSecondaryContainer, fontWeight: 'bold', fontSize: 16 },
  bentoLeft: { marginBottom: 24 },
  statusBox: {
    backgroundColor: 'rgba(0,107,27,0.05)', borderRadius: 24, padding: 24, borderWidth: 1, borderColor: 'rgba(0,107,27,0.1)'
  },
  statusHeader: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 },
  statusBadge: { backgroundColor: C.primaryContainer, paddingHorizontal: 12, paddingVertical: 4, borderRadius: 16 },
  statusBadgeText: { color: C.onPrimaryContainer, fontSize: 12, fontWeight: 'bold' },
  statusTitle: { fontSize: 18, fontWeight: 'bold', color: C.onSurface, marginBottom: 4 },
  statusSub: { fontSize: 14, color: C.onSurfaceVariant },
  listHeader: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'flex-end', marginBottom: 16 },
  listTitle: { fontSize: 24, fontWeight: '900', color: C.onSurface, letterSpacing: -0.5 },
  clearBtnText: { color: C.primary, fontSize: 14, fontWeight: 'bold', textDecorationLine: 'underline' },
  itemCard: {
    backgroundColor: C.surfaceLowest, flexDirection: 'row', alignItems: 'center',
    padding: 12, paddingLeft: 16, borderRadius: 12, marginBottom: 12, marginHorizontal: 24,
    shadowColor: C.onSurface, shadowOffset: { width: 0, height: 4 }, shadowOpacity: 0.04, shadowRadius: 12, elevation: 2,
  },
  itemIconBox: { width: 40, height: 40, borderRadius: 8, backgroundColor: C.surfaceLow, alignItems: 'center', justifyContent: 'center' },
  itemInfo: { flex: 1, marginLeft: 16 },
  itemName: { fontSize: 16, fontWeight: '800', color: C.onSurface },
  itemCategory: { fontSize: 10, textTransform: 'uppercase', fontWeight: 'bold', letterSpacing: 1, color: C.secondary, marginTop: 2 },
  deleteBtn: { padding: 8 },
  missingBox: {
    marginTop: 32, backgroundColor: 'rgba(193,253,124,0.2)', borderRadius: 24, padding: 32,
    alignItems: 'center', borderWidth: 2, borderStyle: 'dashed', borderColor: 'rgba(60,102,0,0.2)'
  },
  missingTitle: { fontSize: 18, fontWeight: 'bold', color: C.onSurface, textAlign: 'center' },
  missingSub: { fontSize: 14, color: C.onSurfaceVariant, textAlign: 'center', marginTop: 8, maxWidth: 250 },
  fabWrapper: { position: 'absolute', bottom: 100, left: 0, right: 0, alignItems: 'flex-end', paddingHorizontal: 24 },
  fab: {
    backgroundColor: C.primary, flexDirection: 'row', alignItems: 'center', gap: 12,
    paddingHorizontal: 32, paddingVertical: 20, borderRadius: 40,
    shadowColor: C.primary, shadowOffset: { width: 0, height: 20 }, shadowOpacity: 0.3, shadowRadius: 50, elevation: 8,
  },
  fabText: { fontSize: 18, fontWeight: '900', color: C.onPrimary, letterSpacing: 0.5 },
});
