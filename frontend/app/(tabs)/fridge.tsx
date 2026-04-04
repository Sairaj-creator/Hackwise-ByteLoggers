import React, { useEffect, useState, useCallback } from 'react';
import { View, Text, StyleSheet, TouchableOpacity, FlatList, TextInput, Modal, RefreshControl, Alert } from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { api } from '@/services/api';
import { Colors, Spacing, Radius, CATEGORIES } from '@/constants/theme';
import { Ionicons } from '@expo/vector-icons';

const STATUS_ORDER: Record<string, number> = { critical: 0, warning: 1, expired: 2, fresh: 3 };
const STATUS_COLORS: Record<string, { bg: string; text: string; icon: string }> = {
  fresh: { bg: Colors.freshBg, text: Colors.fresh, icon: 'checkmark-circle' },
  warning: { bg: Colors.warningBg, text: Colors.warning, icon: 'alert-circle' },
  critical: { bg: Colors.criticalBg, text: Colors.critical, icon: 'flame' },
  expired: { bg: Colors.expiredBg, text: Colors.expired, icon: 'close-circle' },
};

export default function FridgeScreen() {
  const insets = useSafeAreaInsets();
  const [items, setItems] = useState<any[]>([]);
  const [refreshing, setRefreshing] = useState(false);
  const [showAdd, setShowAdd] = useState(false);
  const [name, setName] = useState('');
  const [category, setCategory] = useState('Other');
  const [quantity, setQuantity] = useState('1');
  const [unit, setUnit] = useState('pieces');
  const [expiryDate, setExpiryDate] = useState('');
  const [adding, setAdding] = useState(false);

  const loadItems = useCallback(async () => {
    try {
      const data = await api.getFridge();
      const sorted = (data.ingredients || []).sort((a: any, b: any) => (STATUS_ORDER[a.expiry_status] ?? 3) - (STATUS_ORDER[b.expiry_status] ?? 3));
      setItems(sorted);
    } catch {}
  }, []);

  useEffect(() => { loadItems(); }, [loadItems]);

  const onRefresh = async () => { setRefreshing(true); await loadItems(); setRefreshing(false); };

  const handleAdd = async () => {
    if (!name.trim()) return;
    setAdding(true);
    try {
      await api.addIngredients([{ name: name.trim(), category, quantity: parseFloat(quantity) || 1, unit, expiry_date: expiryDate || undefined }]);
      setShowAdd(false);
      setName(''); setQuantity('1'); setExpiryDate('');
      await loadItems();
    } catch {} finally { setAdding(false); }
  };

  const handleDelete = (itemId: string, itemName: string) => {
    Alert.alert('Delete', `Remove ${itemName} from fridge?`, [
      { text: 'Cancel', style: 'cancel' },
      { text: 'Delete', style: 'destructive', onPress: async () => { await api.deleteFridgeItem(itemId); loadItems(); } },
    ]);
  };

  const renderItem = ({ item }: { item: any }) => {
    const sc = STATUS_COLORS[item.expiry_status] || STATUS_COLORS.fresh;
    return (
      <View testID={`fridge-item-${item.item_id}`} style={styles.itemCard}>
        <View style={[styles.statusDot, { backgroundColor: sc.bg }]}>
          <Ionicons name={sc.icon as any} size={18} color={sc.text} />
        </View>
        <View style={styles.itemInfo}>
          <Text style={styles.itemName}>{item.name}</Text>
          <Text style={styles.itemMeta}>{item.quantity} {item.unit} · {item.category}</Text>
          {item.expiry_date && <Text style={[styles.itemExpiry, { color: sc.text }]}>Exp: {item.expiry_date}</Text>}
        </View>
        <TouchableOpacity testID={`fridge-delete-${item.item_id}`} onPress={() => handleDelete(item.item_id, item.name)} style={styles.deleteBtn}>
          <Ionicons name="trash-outline" size={20} color={Colors.critical} />
        </TouchableOpacity>
      </View>
    );
  };

  return (
    <View style={[styles.container, { paddingTop: insets.top }]}>
      <View style={styles.header}>
        <Text style={styles.title}>My Fridge</Text>
        <TouchableOpacity testID="fridge-add-btn" style={styles.addBtn} onPress={() => setShowAdd(true)}>
          <Ionicons name="add" size={24} color={Colors.textInverse} />
        </TouchableOpacity>
      </View>

      <FlatList
        data={items}
        keyExtractor={(item) => item.item_id}
        renderItem={renderItem}
        contentContainerStyle={styles.list}
        refreshControl={<RefreshControl refreshing={refreshing} onRefresh={onRefresh} tintColor={Colors.orange} />}
        ListEmptyComponent={
          <View style={styles.empty}>
            <Ionicons name="basket-outline" size={64} color={Colors.expired} />
            <Text style={styles.emptyTitle}>Fridge is empty</Text>
            <Text style={styles.emptyText}>Tap + to add your ingredients</Text>
          </View>
        }
      />

      <Modal visible={showAdd} animationType="slide" transparent>
        <View style={styles.modalOverlay}>
          <View style={[styles.modalContent, { paddingBottom: insets.bottom + Spacing.lg }]}>
            <View style={styles.modalHeader}>
              <Text style={styles.modalTitle}>Add Ingredient</Text>
              <TouchableOpacity testID="fridge-modal-close" onPress={() => setShowAdd(false)}>
                <Ionicons name="close" size={28} color={Colors.textPrimary} />
              </TouchableOpacity>
            </View>

            <Text style={styles.label}>Name *</Text>
            <TextInput testID="fridge-name-input" style={styles.input} placeholder="e.g. Tomatoes" placeholderTextColor={Colors.expired} value={name} onChangeText={setName} />

            <Text style={styles.label}>Category</Text>
            <FlatList
              data={CATEGORIES}
              horizontal
              showsHorizontalScrollIndicator={false}
              keyExtractor={(c) => c}
              renderItem={({ item: c }) => (
                <TouchableOpacity testID={`fridge-cat-${c}`} style={[styles.chip, category === c && styles.chipActive]} onPress={() => setCategory(c)}>
                  <Text style={[styles.chipText, category === c && styles.chipTextActive]}>{c}</Text>
                </TouchableOpacity>
              )}
              contentContainerStyle={{ gap: 8, paddingBottom: 8 }}
            />

            <View style={styles.row}>
              <View style={{ flex: 1 }}>
                <Text style={styles.label}>Quantity</Text>
                <TextInput testID="fridge-qty-input" style={styles.input} value={quantity} onChangeText={setQuantity} keyboardType="numeric" />
              </View>
              <View style={{ flex: 1 }}>
                <Text style={styles.label}>Unit</Text>
                <TextInput testID="fridge-unit-input" style={styles.input} value={unit} onChangeText={setUnit} placeholder="pieces" placeholderTextColor={Colors.expired} />
              </View>
            </View>

            <Text style={styles.label}>Expiry Date (YYYY-MM-DD)</Text>
            <TextInput testID="fridge-expiry-input" style={styles.input} placeholder="2026-04-15" placeholderTextColor={Colors.expired} value={expiryDate} onChangeText={setExpiryDate} />

            <TouchableOpacity testID="fridge-submit-btn" style={[styles.submitBtn, adding && { opacity: 0.7 }]} onPress={handleAdd} disabled={adding}>
              <Text style={styles.submitText}>{adding ? 'Adding...' : 'Add to Fridge'}</Text>
            </TouchableOpacity>
          </View>
        </View>
      </Modal>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: Colors.bg },
  header: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', paddingHorizontal: Spacing.lg, paddingVertical: Spacing.md },
  title: { fontSize: 28, fontWeight: '900', color: Colors.textPrimary },
  addBtn: { backgroundColor: Colors.orange, width: 44, height: 44, borderRadius: 22, alignItems: 'center', justifyContent: 'center' },
  list: { paddingHorizontal: Spacing.lg, paddingBottom: Spacing.xxl },
  itemCard: { flexDirection: 'row', alignItems: 'center', backgroundColor: Colors.card, borderRadius: Radius.xl, padding: Spacing.md, marginBottom: Spacing.sm, borderWidth: 1, borderColor: Colors.borderSubtle },
  statusDot: { width: 40, height: 40, borderRadius: 20, alignItems: 'center', justifyContent: 'center' },
  itemInfo: { flex: 1, marginLeft: Spacing.md },
  itemName: { fontSize: 16, fontWeight: '700', color: Colors.textPrimary },
  itemMeta: { fontSize: 12, color: Colors.textSecondary, marginTop: 2 },
  itemExpiry: { fontSize: 12, fontWeight: '600', marginTop: 2 },
  deleteBtn: { padding: 8 },
  empty: { alignItems: 'center', paddingTop: 80 },
  emptyTitle: { fontSize: 18, fontWeight: '700', color: Colors.textPrimary, marginTop: Spacing.md },
  emptyText: { fontSize: 14, color: Colors.textSecondary, marginTop: Spacing.xs },
  modalOverlay: { flex: 1, backgroundColor: 'rgba(0,0,0,0.4)', justifyContent: 'flex-end' },
  modalContent: { backgroundColor: Colors.card, borderTopLeftRadius: Radius.xxl, borderTopRightRadius: Radius.xxl, paddingHorizontal: Spacing.lg, paddingTop: Spacing.lg, maxHeight: '85%' },
  modalHeader: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', marginBottom: Spacing.lg },
  modalTitle: { fontSize: 22, fontWeight: '800', color: Colors.textPrimary },
  label: { fontSize: 13, fontWeight: '600', color: Colors.textSecondary, marginBottom: Spacing.xs, marginTop: Spacing.sm },
  input: { backgroundColor: Colors.inputBg, borderWidth: 1, borderColor: Colors.borderSubtle, borderRadius: Radius.md, paddingHorizontal: 16, paddingVertical: 14, fontSize: 16, color: Colors.textPrimary, marginBottom: Spacing.xs },
  row: { flexDirection: 'row', gap: Spacing.md },
  chip: { paddingHorizontal: 14, paddingVertical: 8, borderRadius: Radius.full, backgroundColor: Colors.inputBg, borderWidth: 1, borderColor: Colors.borderSubtle },
  chipActive: { backgroundColor: Colors.orange, borderColor: Colors.orange },
  chipText: { fontSize: 13, color: Colors.textSecondary, fontWeight: '600' },
  chipTextActive: { color: Colors.textInverse },
  submitBtn: { backgroundColor: Colors.orange, borderRadius: Radius.full, paddingVertical: 16, alignItems: 'center', marginTop: Spacing.lg },
  submitText: { color: Colors.textInverse, fontSize: 17, fontWeight: '700' },
});
