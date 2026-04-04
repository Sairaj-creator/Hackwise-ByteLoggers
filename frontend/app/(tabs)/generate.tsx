import React, { useState, useEffect, useCallback } from 'react';
import { View, Text, StyleSheet, TouchableOpacity, ScrollView, TextInput, ActivityIndicator, Image } from 'react-native';
import { useRouter } from 'expo-router';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { api } from '@/services/api';
import { Colors, Spacing, Radius, CUISINES, DIETS, SPICE_LEVELS, PLACEHOLDER_IMAGES } from '@/constants/theme';
import { Ionicons } from '@expo/vector-icons';

export default function GenerateScreen() {
  const insets = useSafeAreaInsets();
  const router = useRouter();
  const [fridgeItems, setFridgeItems] = useState<any[]>([]);
  const [selectedIngredients, setSelectedIngredients] = useState<string[]>([]);
  const [customIngredient, setCustomIngredient] = useState('');
  const [cuisine, setCuisine] = useState('Any');
  const [diet, setDiet] = useState('None');
  const [spice, setSpice] = useState('Medium');
  const [servings, setServings] = useState(2);
  const [cookTime, setCookTime] = useState('');
  const [generating, setGenerating] = useState(false);
  const [recipe, setRecipe] = useState<any>(null);
  const [error, setError] = useState('');

  const loadFridge = useCallback(async () => {
    try {
      const data = await api.getFridge();
      setFridgeItems(data.ingredients || []);
    } catch {}
  }, []);

  useEffect(() => { loadFridge(); }, [loadFridge]);

  const toggleIngredient = (name: string) => {
    setSelectedIngredients(prev => prev.includes(name) ? prev.filter(n => n !== name) : [...prev, name]);
  };

  const addCustom = () => {
    if (customIngredient.trim() && !selectedIngredients.includes(customIngredient.trim())) {
      setSelectedIngredients(prev => [...prev, customIngredient.trim()]);
      setCustomIngredient('');
    }
  };

  const handleGenerate = async () => {
    if (selectedIngredients.length === 0) { setError('Please select at least one ingredient'); return; }
    setError('');
    setGenerating(true);
    setRecipe(null);
    try {
      const data = await api.generateRecipe({
        ingredients: selectedIngredients,
        servings,
        preferences: {
          cuisine: cuisine === 'Any' ? '' : cuisine,
          dietary: diet === 'None' ? '' : diet,
          max_time_minutes: cookTime ? cookTime : '30',
          spice_level: spice.toLowerCase(),
        },
      });
      setRecipe(data.recipe || data);
    } catch (e: any) {
      setError(e.message || 'Generation failed');
    } finally {
      setGenerating(false);
    }
  };

  if (recipe) {
    return (
      <ScrollView style={[styles.container, { paddingTop: insets.top }]} contentContainerStyle={styles.content}>
        <View style={styles.resultHeader}>
          <TouchableOpacity testID="generate-back-btn" onPress={() => setRecipe(null)} style={styles.backBtn}>
            <Ionicons name="arrow-back" size={24} color={Colors.textPrimary} />
          </TouchableOpacity>
          <Text style={styles.resultTitle}>Recipe Generated!</Text>
        </View>

        <Image source={{ uri: PLACEHOLDER_IMAGES[0] }} style={styles.recipeImage} />

        <Text style={styles.recipeTitle}>{recipe.title}</Text>
        <Text style={styles.recipeDesc}>{recipe.cuisine} · {recipe.difficulty}</Text>

        <View style={styles.badgeRow}>
          <View style={styles.badge}><Ionicons name="time-outline" size={14} color={Colors.orange} /><Text style={styles.badgeText}>{recipe.estimated_time_minutes} min</Text></View>
          <View style={styles.badge}><Ionicons name="people-outline" size={14} color={Colors.orange} /><Text style={styles.badgeText}>{recipe.servings} servings</Text></View>
          <View style={styles.badge}><Ionicons name="fitness-outline" size={14} color={Colors.orange} /><Text style={styles.badgeText}>{recipe.difficulty}</Text></View>
        </View>

        <TouchableOpacity testID="generate-view-full-btn" style={styles.viewFullBtn} onPress={() => router.push(`/recipe/${recipe.recipe_id}`)}>
          <Text style={styles.viewFullText}>View Full Recipe</Text>
          <Ionicons name="arrow-forward" size={18} color={Colors.textInverse} />
        </TouchableOpacity>

        <TouchableOpacity testID="generate-new-btn" style={styles.newBtn} onPress={() => setRecipe(null)}>
          <Ionicons name="refresh" size={18} color={Colors.orange} />
          <Text style={styles.newBtnText}>Generate Another</Text>
        </TouchableOpacity>
      </ScrollView>
    );
  }

  return (
    <ScrollView style={[styles.container, { paddingTop: insets.top }]} contentContainerStyle={styles.content} keyboardShouldPersistTaps="handled">
      <Text style={styles.title}>Generate Recipe</Text>
      <Text style={styles.subtitle}>Select ingredients and preferences</Text>

      {error ? (
        <View style={styles.errorBox}>
          <Text style={styles.errorText}>{error}</Text>
        </View>
      ) : null}

      {/* Fridge Ingredients */}
      {fridgeItems.length > 0 && (
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>From Your Fridge</Text>
          <View style={styles.chipWrap}>
            {fridgeItems.map(item => (
              <TouchableOpacity key={item.item_id} testID={`gen-ingredient-${item.item_id}`} style={[styles.chip, selectedIngredients.includes(item.name) && styles.chipActive]} onPress={() => toggleIngredient(item.name)}>
                <Text style={[styles.chipText, selectedIngredients.includes(item.name) && styles.chipTextActive]}>{item.name}</Text>
                {selectedIngredients.includes(item.name) && <Ionicons name="checkmark" size={14} color={Colors.textInverse} />}
              </TouchableOpacity>
            ))}
          </View>
        </View>
      )}

      {/* Custom Ingredient */}
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>Add Ingredient</Text>
        <View style={styles.addRow}>
          <TextInput testID="gen-custom-input" style={[styles.input, { flex: 1 }]} placeholder="Type ingredient..." placeholderTextColor={Colors.expired} value={customIngredient} onChangeText={setCustomIngredient} onSubmitEditing={addCustom} />
          <TouchableOpacity testID="gen-custom-add" style={styles.addChipBtn} onPress={addCustom}>
            <Ionicons name="add" size={22} color={Colors.textInverse} />
          </TouchableOpacity>
        </View>
        {selectedIngredients.length > 0 && (
          <View style={styles.selectedWrap}>
            {selectedIngredients.filter(n => !fridgeItems.find(i => i.name === n)).map(n => (
              <View key={n} style={[styles.chip, styles.chipActive]}>
                <Text style={styles.chipTextActive}>{n}</Text>
                <TouchableOpacity onPress={() => toggleIngredient(n)}><Ionicons name="close" size={14} color={Colors.textInverse} /></TouchableOpacity>
              </View>
            ))}
          </View>
        )}
      </View>

      {/* Preferences */}
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>Cuisine</Text>
        <ScrollView horizontal showsHorizontalScrollIndicator={false}>
          <View style={styles.chipRow}>
            {CUISINES.map(c => (
              <TouchableOpacity key={c} testID={`gen-cuisine-${c}`} style={[styles.chip, cuisine === c && styles.chipActive]} onPress={() => setCuisine(c)}>
                <Text style={[styles.chipText, cuisine === c && styles.chipTextActive]}>{c}</Text>
              </TouchableOpacity>
            ))}
          </View>
        </ScrollView>
      </View>

      <View style={styles.section}>
        <Text style={styles.sectionTitle}>Diet</Text>
        <ScrollView horizontal showsHorizontalScrollIndicator={false}>
          <View style={styles.chipRow}>
            {DIETS.map(d => (
              <TouchableOpacity key={d} testID={`gen-diet-${d}`} style={[styles.chip, diet === d && styles.chipActive]} onPress={() => setDiet(d)}>
                <Text style={[styles.chipText, diet === d && styles.chipTextActive]}>{d}</Text>
              </TouchableOpacity>
            ))}
          </View>
        </ScrollView>
      </View>

      <View style={styles.section}>
        <Text style={styles.sectionTitle}>Spice Level</Text>
        <View style={styles.chipRow}>
          {SPICE_LEVELS.map(s => (
            <TouchableOpacity key={s} testID={`gen-spice-${s}`} style={[styles.chip, spice === s && styles.chipActive]} onPress={() => setSpice(s)}>
              <Text style={[styles.chipText, spice === s && styles.chipTextActive]}>{s}</Text>
            </TouchableOpacity>
          ))}
        </View>
      </View>

      <View style={styles.rowSection}>
        <View style={{ flex: 1 }}>
          <Text style={styles.sectionTitle}>Servings</Text>
          <View style={styles.counterRow}>
            <TouchableOpacity testID="gen-servings-minus" style={styles.counterBtn} onPress={() => setServings(Math.max(1, servings - 1))}>
              <Ionicons name="remove" size={20} color={Colors.textPrimary} />
            </TouchableOpacity>
            <Text style={styles.counterValue}>{servings}</Text>
            <TouchableOpacity testID="gen-servings-plus" style={styles.counterBtn} onPress={() => setServings(servings + 1)}>
              <Ionicons name="add" size={20} color={Colors.textPrimary} />
            </TouchableOpacity>
          </View>
        </View>
        <View style={{ flex: 1 }}>
          <Text style={styles.sectionTitle}>Max Time (min)</Text>
          <TextInput testID="gen-time-input" style={styles.input} placeholder="No limit" placeholderTextColor={Colors.expired} value={cookTime} onChangeText={setCookTime} keyboardType="numeric" />
        </View>
      </View>

      <TouchableOpacity testID="gen-submit-btn" style={[styles.generateBtn, generating && { opacity: 0.7 }]} onPress={handleGenerate} disabled={generating} activeOpacity={0.85}>
        {generating ? (
          <View style={styles.genLoadRow}>
            <ActivityIndicator color={Colors.textInverse} />
            <Text style={styles.generateText}>Creating your recipe...</Text>
          </View>
        ) : (
          <View style={styles.genLoadRow}>
            <Ionicons name="sparkles" size={22} color={Colors.textInverse} />
            <Text style={styles.generateText}>Generate Recipe</Text>
          </View>
        )}
      </TouchableOpacity>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: Colors.bg },
  content: { paddingHorizontal: Spacing.lg, paddingBottom: Spacing.xxl },
  title: { fontSize: 28, fontWeight: '900', color: Colors.textPrimary, marginTop: Spacing.md },
  subtitle: { fontSize: 15, color: Colors.textSecondary, marginTop: Spacing.xs, marginBottom: Spacing.lg },
  errorBox: { backgroundColor: Colors.criticalBg, padding: Spacing.md, borderRadius: Radius.md, marginBottom: Spacing.md },
  errorText: { color: Colors.critical, fontSize: 14 },
  section: { marginBottom: Spacing.lg },
  sectionTitle: { fontSize: 15, fontWeight: '700', color: Colors.textPrimary, marginBottom: Spacing.sm },
  chipWrap: { flexDirection: 'row', flexWrap: 'wrap', gap: 8 },
  chipRow: { flexDirection: 'row', gap: 8 },
  chip: { paddingHorizontal: 14, paddingVertical: 10, borderRadius: Radius.full, backgroundColor: Colors.inputBg, borderWidth: 1, borderColor: Colors.borderSubtle, flexDirection: 'row', alignItems: 'center', gap: 4 },
  chipActive: { backgroundColor: Colors.orange, borderColor: Colors.orange },
  chipText: { fontSize: 14, color: Colors.textSecondary, fontWeight: '600' },
  chipTextActive: { color: Colors.textInverse, fontSize: 14, fontWeight: '600' },
  addRow: { flexDirection: 'row', gap: Spacing.sm },
  input: { backgroundColor: Colors.inputBg, borderWidth: 1, borderColor: Colors.borderSubtle, borderRadius: Radius.md, paddingHorizontal: 16, paddingVertical: 14, fontSize: 16, color: Colors.textPrimary },
  addChipBtn: { backgroundColor: Colors.orange, width: 48, borderRadius: Radius.md, alignItems: 'center', justifyContent: 'center' },
  selectedWrap: { flexDirection: 'row', flexWrap: 'wrap', gap: 8, marginTop: Spacing.sm },
  rowSection: { flexDirection: 'row', gap: Spacing.lg, marginBottom: Spacing.lg },
  counterRow: { flexDirection: 'row', alignItems: 'center', gap: Spacing.md },
  counterBtn: { width: 40, height: 40, borderRadius: 20, backgroundColor: Colors.inputBg, alignItems: 'center', justifyContent: 'center', borderWidth: 1, borderColor: Colors.borderSubtle },
  counterValue: { fontSize: 22, fontWeight: '800', color: Colors.textPrimary, minWidth: 30, textAlign: 'center' },
  generateBtn: { backgroundColor: Colors.orange, borderRadius: Radius.full, paddingVertical: 18, alignItems: 'center', marginTop: Spacing.md },
  generateText: { color: Colors.textInverse, fontSize: 18, fontWeight: '700' },
  genLoadRow: { flexDirection: 'row', alignItems: 'center', gap: 10 },
  // Result styles
  resultHeader: { flexDirection: 'row', alignItems: 'center', marginTop: Spacing.md, marginBottom: Spacing.lg },
  backBtn: { width: 44, height: 44, justifyContent: 'center' },
  resultTitle: { fontSize: 20, fontWeight: '800', color: Colors.textPrimary },
  recipeImage: { width: '100%', height: 200, borderRadius: Radius.xl, marginBottom: Spacing.lg },
  recipeTitle: { fontSize: 26, fontWeight: '900', color: Colors.textPrimary },
  recipeDesc: { fontSize: 15, color: Colors.textSecondary, marginTop: Spacing.xs, lineHeight: 22 },
  badgeRow: { flexDirection: 'row', gap: Spacing.sm, marginTop: Spacing.md },
  badge: { flexDirection: 'row', alignItems: 'center', gap: 4, backgroundColor: Colors.inputBg, paddingHorizontal: 12, paddingVertical: 8, borderRadius: Radius.full },
  badgeText: { fontSize: 13, color: Colors.textSecondary, fontWeight: '600' },
  viewFullBtn: { backgroundColor: Colors.orange, borderRadius: Radius.full, paddingVertical: 16, flexDirection: 'row', alignItems: 'center', justifyContent: 'center', gap: 8, marginTop: Spacing.xl },
  viewFullText: { color: Colors.textInverse, fontSize: 17, fontWeight: '700' },
  newBtn: { flexDirection: 'row', alignItems: 'center', justifyContent: 'center', gap: 8, paddingVertical: 16, marginTop: Spacing.sm },
  newBtnText: { color: Colors.orange, fontSize: 16, fontWeight: '600' },
});
