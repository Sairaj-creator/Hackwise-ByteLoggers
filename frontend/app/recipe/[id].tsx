import React, { useEffect, useState } from 'react';
import { View, Text, StyleSheet, TouchableOpacity, ScrollView, Image, ActivityIndicator } from 'react-native';
import { useLocalSearchParams, useRouter } from 'expo-router';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { api } from '@/services/api';
import { Colors, Spacing, Radius, PLACEHOLDER_IMAGES } from '@/constants/theme';
import { Ionicons } from '@expo/vector-icons';

export default function RecipeDetailScreen() {
  const { id } = useLocalSearchParams<{ id: string }>();
  const insets = useSafeAreaInsets();
  const router = useRouter();
  const [recipe, setRecipe] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [favorited, setFavorited] = useState(false);

  useEffect(() => {
    (async () => {
      try {
        const data = await api.getRecipe(id!);
        setRecipe(data);
        setFavorited(data.is_favorited || false);
      } catch {} finally { setLoading(false); }
    })();
  }, [id]);

  const handleFavorite = async () => {
    try {
      const data = await api.toggleFavorite(id!);
      setFavorited(data.favorited);
    } catch {}
  };

  if (loading) {
    return <View style={styles.loadingView}><ActivityIndicator size="large" color={Colors.orange} /></View>;
  }

  if (!recipe) {
    return (
      <View style={styles.loadingView}>
        <Text style={styles.errorText}>Recipe not found</Text>
        <TouchableOpacity onPress={() => router.back()}><Text style={styles.backLink}>Go back</Text></TouchableOpacity>
      </View>
    );
  }

  return (
    <View style={styles.container}>
      <ScrollView contentContainerStyle={{ paddingBottom: 100 }}>
        <Image source={{ uri: PLACEHOLDER_IMAGES[0] }} style={styles.heroImage} />

        <TouchableOpacity testID="recipe-back-btn" style={[styles.backBtn, { top: insets.top + 8 }]} onPress={() => router.back()}>
          <Ionicons name="arrow-back" size={24} color={Colors.textPrimary} />
        </TouchableOpacity>

        <TouchableOpacity testID="recipe-fav-btn" style={[styles.favBtn, { top: insets.top + 8 }]} onPress={handleFavorite}>
          <Ionicons name={favorited ? 'heart' : 'heart-outline'} size={24} color={favorited ? Colors.critical : Colors.textPrimary} />
        </TouchableOpacity>

        <View style={styles.content}>
          <Text style={styles.title}>{recipe.title}</Text>
          <Text style={styles.description}>{recipe.description}</Text>

          <View style={styles.metaRow}>
            <View style={styles.metaItem}><Ionicons name="time-outline" size={18} color={Colors.orange} /><Text style={styles.metaValue}>{recipe.total_time_minutes || recipe.cook_time_minutes} min</Text></View>
            <View style={styles.metaItem}><Ionicons name="people-outline" size={18} color={Colors.orange} /><Text style={styles.metaValue}>{recipe.servings} servings</Text></View>
            <View style={styles.metaItem}><Ionicons name="fitness-outline" size={18} color={Colors.orange} /><Text style={styles.metaValue}>{recipe.difficulty}</Text></View>
            <View style={styles.metaItem}><Ionicons name="restaurant-outline" size={18} color={Colors.orange} /><Text style={styles.metaValue}>{recipe.cuisine}</Text></View>
          </View>

          {/* Tags */}
          {recipe.tags?.length > 0 && (
            <View style={styles.tagRow}>
              {recipe.tags.map((tag: string) => (
                <View key={tag} style={styles.tag}><Text style={styles.tagText}>{tag}</Text></View>
              ))}
            </View>
          )}

          {/* Ingredients */}
          <Text style={styles.sectionTitle}>Ingredients</Text>
          {(recipe.ingredients || []).map((ing: any, i: number) => (
            <View key={i} style={styles.ingredientRow}>
              <View style={[styles.ingredientDot, ing.from_fridge ? styles.dotFridge : styles.dotExtra]} />
              <Text style={styles.ingredientText}>
                {ing.quantity} {ing.unit} {ing.name}
              </Text>
              {ing.from_fridge && <View style={styles.fridgeBadge}><Text style={styles.fridgeBadgeText}>Fridge</Text></View>}
            </View>
          ))}

          {/* Steps */}
          <Text style={styles.sectionTitle}>Steps</Text>
          {(recipe.steps || []).map((step: any, i: number) => (
            <View key={i} style={styles.stepCard}>
              <View style={styles.stepNumber}><Text style={styles.stepNumberText}>{step.step_number || i + 1}</Text></View>
              <View style={styles.stepContent}>
                <Text style={styles.stepText}>{step.instruction}</Text>
                {step.timer_seconds && (
                  <View style={styles.timerBadge}>
                    <Ionicons name="timer-outline" size={14} color={Colors.orange} />
                    <Text style={styles.timerText}>{Math.round(step.timer_seconds / 60)} min</Text>
                  </View>
                )}
              </View>
            </View>
          ))}

          {/* Nutrition */}
          {recipe.nutrition_per_serving && (
            <>
              <Text style={styles.sectionTitle}>Nutrition (per serving)</Text>
              <View style={styles.nutritionGrid}>
                <View style={styles.nutrientCard}><Text style={styles.nutrientValue}>{recipe.nutrition_per_serving.calories}</Text><Text style={styles.nutrientLabel}>Calories</Text></View>
                <View style={styles.nutrientCard}><Text style={styles.nutrientValue}>{recipe.nutrition_per_serving.protein_g}g</Text><Text style={styles.nutrientLabel}>Protein</Text></View>
                <View style={styles.nutrientCard}><Text style={styles.nutrientValue}>{recipe.nutrition_per_serving.carbs_g}g</Text><Text style={styles.nutrientLabel}>Carbs</Text></View>
                <View style={styles.nutrientCard}><Text style={styles.nutrientValue}>{recipe.nutrition_per_serving.fat_g}g</Text><Text style={styles.nutrientLabel}>Fat</Text></View>
              </View>
            </>
          )}

          {/* Tips */}
          {recipe.tips?.length > 0 && (
            <>
              <Text style={styles.sectionTitle}>Tips</Text>
              {recipe.tips.map((tip: string, i: number) => (
                <View key={i} style={styles.tipRow}>
                  <Ionicons name="bulb-outline" size={16} color={Colors.amber} />
                  <Text style={styles.tipText}>{tip}</Text>
                </View>
              ))}
            </>
          )}
        </View>
      </ScrollView>

      {/* Bottom CTA */}
      <View style={[styles.bottomBar, { paddingBottom: insets.bottom + Spacing.md }]}>
        <TouchableOpacity testID="recipe-start-cooking-btn" style={styles.cookBtn} onPress={() => router.push(`/cooking/${recipe.recipe_id}`)} activeOpacity={0.85}>
          <Ionicons name="flame" size={22} color={Colors.textInverse} />
          <Text style={styles.cookBtnText}>Start Cooking</Text>
        </TouchableOpacity>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: Colors.bg },
  loadingView: { flex: 1, justifyContent: 'center', alignItems: 'center', backgroundColor: Colors.bg },
  errorText: { fontSize: 16, color: Colors.textSecondary },
  backLink: { color: Colors.orange, fontSize: 16, fontWeight: '600', marginTop: 8 },
  heroImage: { width: '100%', height: 260 },
  backBtn: { position: 'absolute', left: 16, width: 40, height: 40, borderRadius: 20, backgroundColor: 'rgba(255,255,255,0.9)', alignItems: 'center', justifyContent: 'center' },
  favBtn: { position: 'absolute', right: 16, width: 40, height: 40, borderRadius: 20, backgroundColor: 'rgba(255,255,255,0.9)', alignItems: 'center', justifyContent: 'center' },
  content: { paddingHorizontal: Spacing.lg, paddingTop: Spacing.lg },
  title: { fontSize: 28, fontWeight: '900', color: Colors.textPrimary, letterSpacing: -0.5 },
  description: { fontSize: 15, color: Colors.textSecondary, marginTop: Spacing.xs, lineHeight: 22 },
  metaRow: { flexDirection: 'row', flexWrap: 'wrap', gap: Spacing.md, marginTop: Spacing.lg },
  metaItem: { flexDirection: 'row', alignItems: 'center', gap: 6 },
  metaValue: { fontSize: 14, fontWeight: '600', color: Colors.textSecondary },
  tagRow: { flexDirection: 'row', flexWrap: 'wrap', gap: 6, marginTop: Spacing.md },
  tag: { backgroundColor: Colors.inputBg, paddingHorizontal: 10, paddingVertical: 5, borderRadius: Radius.full },
  tagText: { fontSize: 12, color: Colors.textSecondary, fontWeight: '600' },
  sectionTitle: { fontSize: 20, fontWeight: '800', color: Colors.textPrimary, marginTop: Spacing.xl, marginBottom: Spacing.md },
  ingredientRow: { flexDirection: 'row', alignItems: 'center', paddingVertical: 10, borderBottomWidth: 1, borderBottomColor: Colors.borderSubtle },
  ingredientDot: { width: 8, height: 8, borderRadius: 4, marginRight: 12 },
  dotFridge: { backgroundColor: Colors.fresh },
  dotExtra: { backgroundColor: Colors.expired },
  ingredientText: { flex: 1, fontSize: 15, color: Colors.textPrimary },
  fridgeBadge: { backgroundColor: Colors.freshBg, paddingHorizontal: 8, paddingVertical: 2, borderRadius: Radius.full },
  fridgeBadgeText: { fontSize: 11, color: Colors.fresh, fontWeight: '700' },
  stepCard: { flexDirection: 'row', marginBottom: Spacing.md },
  stepNumber: { width: 32, height: 32, borderRadius: 16, backgroundColor: Colors.orange, alignItems: 'center', justifyContent: 'center', marginRight: 12, marginTop: 2 },
  stepNumberText: { color: Colors.textInverse, fontSize: 14, fontWeight: '800' },
  stepContent: { flex: 1 },
  stepText: { fontSize: 15, color: Colors.textPrimary, lineHeight: 22 },
  timerBadge: { flexDirection: 'row', alignItems: 'center', gap: 4, marginTop: 6, backgroundColor: Colors.inputBg, paddingHorizontal: 10, paddingVertical: 4, borderRadius: Radius.full, alignSelf: 'flex-start' },
  timerText: { fontSize: 12, color: Colors.orange, fontWeight: '600' },
  nutritionGrid: { flexDirection: 'row', gap: Spacing.sm },
  nutrientCard: { flex: 1, backgroundColor: Colors.card, borderRadius: Radius.lg, padding: Spacing.md, alignItems: 'center', borderWidth: 1, borderColor: Colors.borderSubtle },
  nutrientValue: { fontSize: 20, fontWeight: '900', color: Colors.orange },
  nutrientLabel: { fontSize: 11, color: Colors.textSecondary, fontWeight: '600', marginTop: 2 },
  tipRow: { flexDirection: 'row', gap: 8, marginBottom: 8, alignItems: 'flex-start' },
  tipText: { fontSize: 14, color: Colors.textSecondary, flex: 1, lineHeight: 20 },
  bottomBar: { position: 'absolute', bottom: 0, left: 0, right: 0, backgroundColor: Colors.card, borderTopWidth: 1, borderTopColor: Colors.borderSubtle, paddingHorizontal: Spacing.lg, paddingTop: Spacing.md },
  cookBtn: { backgroundColor: Colors.orange, borderRadius: Radius.full, paddingVertical: 16, flexDirection: 'row', alignItems: 'center', justifyContent: 'center', gap: 8 },
  cookBtnText: { color: Colors.textInverse, fontSize: 18, fontWeight: '700' },
});
