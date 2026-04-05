import React, { useEffect, useState } from 'react';
import { View, Text, StyleSheet, TouchableOpacity, ScrollView, Image, ActivityIndicator } from 'react-native';
import { useLocalSearchParams, useRouter } from 'expo-router';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { api } from '@/services/api';
import { Ionicons } from '@expo/vector-icons';

const C = {
  surface: '#f6f6f6',
  onSurface: '#2d2f2f',
  onSurfaceVariant: '#5a5c5c',
  primary: '#006b1b',
  onPrimary: '#d1ffc8',
  primaryContainer: '#91f78e',
  onPrimaryContainer: '#005e17',
  secondary: '#874e00',
  secondaryContainer: '#ffc791',
  onSecondaryContainer: '#6a3c00',
  tertiary: '#3c6600',
  tertiaryContainer: '#c1fd7c',
  onTertiaryContainer: '#396100',
  errorContainer: '#f95630',
  onError: '#ffefec',
  surfaceContainerLow: '#f0f1f1',
  surfaceContainerLowest: '#ffffff',
  outlineVariant: '#acadad',
};

const DEFAULT_IMG = 'https://lh3.googleusercontent.com/aida-public/AB6AXuBbyb4NzaBMLL-TORS0tEQ-I0HL8643-LriZ7dFHfsLDAF1KuZNAH0d2KKHSY6pupNADWyyVYhDOvvHGX30sh8-tECjctbaiRpQf31J6FnSZB7VNtmEztUGDBNfh4FRmAnLV_ODrragf5xvD37OEMm3UkR6kKAdLSnfJvWj0pXwgjnDdCEn_gwovCmh1vQUfmOe1tpU8LAT6DrLTgbvloI-NHKP6YGUwzY7PU2IsrcP12KnCyWEnL9CtrpRp9BwuhrUTzu9DFBtH-ge';

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
    return <View style={styles.loadingView}><ActivityIndicator size="large" color={C.primary} /></View>;
  }

  if (!recipe) {
    return (
      <View style={styles.loadingView}>
        <Text style={{color: C.onSurfaceVariant}}>Recipe not found</Text>
        <TouchableOpacity onPress={() => router.back()}><Text style={{color: C.primary, fontWeight:'bold', marginTop: 8}}>Go back</Text></TouchableOpacity>
      </View>
    );
  }

  return (
    <View style={[styles.container, { paddingTop: insets.top }]}>
      {/* TopAppBar */}
      <View style={styles.appBar}>
        <View style={styles.appBarLeft}>
          <TouchableOpacity testID="recipe-back-btn" onPress={() => router.back()} style={styles.iconBtn}>
            <Ionicons name="arrow-back" size={24} color={C.primary} />
          </TouchableOpacity>
          <Text style={styles.appBarTitle}>Ingredia</Text>
        </View>
        <View style={styles.appBarRight}>
          <TouchableOpacity testID="recipe-fav-btn" onPress={handleFavorite} style={styles.iconBtn}>
            <Ionicons name={favorited ? 'heart' : 'heart-outline'} size={24} color={favorited ? C.primary : C.primary} />
          </TouchableOpacity>
          <TouchableOpacity style={styles.iconBtn}>
            <Ionicons name="share-social-outline" size={24} color={C.onSurfaceVariant} />
          </TouchableOpacity>
        </View>
      </View>

      <ScrollView contentContainerStyle={styles.contentWrap}>
        {/* Hero Section */}
        <View style={styles.heroWrap}>
          <Image source={{ uri: recipe.image_url || DEFAULT_IMG }} style={styles.heroImage} />
          <View style={styles.heroContentRow}>
            <View style={styles.heroTitleBox}>
              <Text style={styles.heroTitle}>{recipe.title}</Text>
              <Text style={styles.heroMeta}>{recipe.difficulty?.toUpperCase()} • {recipe.estimated_time_minutes} MINS</Text>
            </View>
            <TouchableOpacity style={styles.playBtn}>
              <Ionicons name="play" size={24} color={C.onError} />
            </TouchableOpacity>
          </View>
        </View>

        {/* Content Layout */}
        <View style={styles.mainGrid}>
          {/* Left Column (Description & Ingredients) */}
          <View style={styles.leftCol}>
            {/* The Dish Identity */}
            <View style={styles.section}>
              <Text style={styles.sectionTitle}>The Dish Identity</Text>
              <Text style={styles.dishDescription}>
                "{recipe.description || 'A sophisticated balance of flavors. This recipe utilizes modern techniques to maximize nutrient absorption while maintaining a restaurant-quality aesthetic.'}"
              </Text>
            </View>

            {/* Nutrient Tracker */}
            {recipe.nutrition_per_serving && (
              <View style={styles.bentoGrid}>
                <View style={styles.bentoCard}>
                  <Text style={[styles.bentoVal, {color: C.primary}]}>{recipe.nutrition_per_serving.calories}</Text>
                  <Text style={styles.bentoLabel}>CALORIES</Text>
                </View>
                <View style={styles.bentoCard}>
                  <Text style={[styles.bentoVal, {color: C.secondary}]}>{recipe.nutrition_per_serving.protein_g}g</Text>
                  <Text style={styles.bentoLabel}>PROTEIN</Text>
                </View>
                <View style={styles.bentoCard}>
                  <Text style={[styles.bentoVal, {color: C.tertiary}]}>{recipe.nutrition_per_serving.fiber_g || '12'}g</Text>
                  <Text style={styles.bentoLabel}>FIBER</Text>
                </View>
                <View style={styles.bentoCard}>
                  <Text style={[styles.bentoVal, {color: C.onSurface}]}>{recipe.nutrition_per_serving.carbs_g}g</Text>
                  <Text style={styles.bentoLabel}>CARBS</Text>
                </View>
              </View>
            )}

            {/* Ingredients */}
            <View style={styles.section}>
              <View style={styles.ingredientsHeader}>
                <Text style={styles.sectionTitle}>The Elements</Text>
                <View style={styles.servingsBadge}>
                  <Text style={styles.servingsText}>{recipe.servings} SERVINGS</Text>
                </View>
              </View>
              
              <View style={styles.ingredientsList}>
                {(recipe.ingredients || []).map((ing: any, idx: number) => (
                  <View key={idx} style={styles.ingredientRow}>
                    <Text style={styles.ingName}>{ing.name}</Text>
                    <Text style={styles.ingQuant}>{ing.quantity} {ing.unit}</Text>
                  </View>
                ))}
              </View>
            </View>
          </View>

          {/* Right Column (Instructions) */}
          <View style={styles.rightCol}>
            <View style={styles.instructionsBox}>
              <Text style={[styles.sectionTitle, {marginBottom: 24}]}>Culinary Protocol</Text>
              
              <View style={styles.stepsWrap}>
                {(recipe.steps || []).map((step: any, idx: number) => (
                  <View key={idx} style={styles.stepRow}>
                    <View style={styles.stepNumWrap}>
                      <Text style={styles.stepNum}>{step.step || idx + 1}</Text>
                    </View>
                    <View style={styles.stepTextWrap}>
                      <Text style={styles.stepTitle}>Step {step.step || idx + 1}</Text>
                      <Text style={styles.stepDesc}>{step.instruction}</Text>
                    </View>
                  </View>
                ))}
              </View>
              
              <View style={styles.startGuidedWrap}>
                <TouchableOpacity testID="recipe-start-cooking-btn" style={styles.startGuidedBtn} onPress={() => router.push(`/cooking/${recipe.recipe_id}`)}>
                  <Ionicons name="timer" size={20} color={C.onPrimary} />
                  <Text style={styles.startGuidedText}>Start Guided Session</Text>
                </TouchableOpacity>
              </View>
            </View>
          </View>
        </View>

        {/* Masterclass CTA */}
        <View style={styles.masterclassBox}>
          <View style={styles.mcLeft}>
            <View style={styles.mcIconWrap}>
              <Ionicons name="videocam" size={32} color={C.errorContainer} />
            </View>
            <View style={styles.mcTexts}>
              <Text style={styles.mcTitle}>Watch the Masterclass</Text>
              <Text style={styles.mcDesc}>Follow Chef's visual guide.</Text>
            </View>
          </View>
          <TouchableOpacity style={styles.mcBtn}>
            <Text style={styles.mcBtnText}>Watch on YouTube</Text>
          </TouchableOpacity>
        </View>

      </ScrollView>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: C.surface },
  loadingView: { flex: 1, justifyContent: 'center', alignItems: 'center', backgroundColor: C.surface },
  
  appBar: {
    flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center',
    paddingHorizontal: 24, paddingVertical: 16, backgroundColor: C.surface,
  },
  appBarLeft: { flexDirection: 'row', alignItems: 'center', gap: 12 },
  appBarRight: { flexDirection: 'row', alignItems: 'center', gap: 16 },
  iconBtn: { padding: 4 },
  appBarTitle: { fontSize: 24, fontWeight: 'bold', fontStyle: 'italic', color: C.primary, letterSpacing: -0.5 },
  
  contentWrap: { paddingBottom: 120 },
  
  heroWrap: { paddingHorizontal: 24, paddingVertical: 16, position: 'relative' },
  heroImage: { width: '100%', height: 400, borderRadius: 24, backgroundColor: C.surfaceContainerLow },
  heroContentRow: {
    position: 'absolute', bottom: 40, left: 48, right: 48,
    flexDirection: 'row', justifyContent: 'space-between', alignItems: 'flex-end',
  },
  heroTitleBox: {
    backgroundColor: 'rgba(255,255,255,0.7)', padding: 16, borderRadius: 12, maxWidth: '80%', overflow: 'hidden'
  },
  heroTitle: { fontSize: 28, fontWeight: '900', color: C.onSurface, letterSpacing: -0.5, marginBottom: 4 },
  heroMeta: { fontSize: 12, fontWeight: 'bold', color: C.primary, letterSpacing: 1 },
  playBtn: {
    width: 56, height: 56, borderRadius: 28, backgroundColor: C.errorContainer,
    alignItems: 'center', justifyContent: 'center', shadowColor: '#000', shadowOpacity: 0.2, shadowRadius: 10, elevation: 5,
  },

  mainGrid: { paddingHorizontal: 24, marginTop: 16 },
  leftCol: { marginBottom: 32 },
  rightCol: {},
  
  section: { marginBottom: 48 },
  sectionTitle: { fontSize: 24, fontWeight: 'bold', color: C.onSurface, marginBottom: 16 },
  dishDescription: { fontSize: 18, fontStyle: 'italic', color: C.onSurfaceVariant, lineHeight: 28 },
  
  bentoGrid: { flexDirection: 'row', flexWrap: 'wrap', gap: 16, marginBottom: 48 },
  bentoCard: {
    flex: 1, minWidth: '40%', backgroundColor: C.surfaceContainerLow, borderRadius: 16,
    padding: 16, alignItems: 'center', justifyContent: 'center', gap: 4
  },
  bentoVal: { fontSize: 24, fontWeight: 'bold' },
  bentoLabel: { fontSize: 10, fontWeight: 'bold', color: C.onSurfaceVariant, letterSpacing: 1 },
  
  ingredientsHeader: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', marginBottom: 24 },
  servingsBadge: { backgroundColor: C.primaryContainer, paddingHorizontal: 16, paddingVertical: 4, borderRadius: 16 },
  servingsText: { fontSize: 12, fontWeight: 'bold', color: C.onPrimaryContainer },
  ingredientsList: { flexDirection: 'row', flexWrap: 'wrap', justifyContent: 'space-between' },
  ingredientRow: {
    width: '48%', flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center',
    paddingVertical: 12, borderBottomWidth: 1, borderBottomColor: 'rgba(172,173,173,0.2)',
  },
  ingName: { fontSize: 14, color: C.onSurface },
  ingQuant: { fontSize: 14, fontWeight: 'bold', color: C.primary },

  instructionsBox: {
    backgroundColor: C.surfaceContainerLowest, padding: 32, borderRadius: 24,
    shadowColor: '#000', shadowOpacity: 0.04, shadowRadius: 20, elevation: 2, marginBottom: 32
  },
  stepsWrap: { gap: 40 },
  stepRow: { flexDirection: 'row', gap: 24 },
  stepNumWrap: {
    width: 32, height: 32, borderRadius: 16, backgroundColor: C.primary,
    alignItems: 'center', justifyContent: 'center', marginTop: 2
  },
  stepNum: { color: C.surfaceContainerLowest, fontSize: 14, fontWeight: 'bold' },
  stepTextWrap: { flex: 1 },
  stepTitle: { fontSize: 16, fontWeight: 'bold', color: C.onSurface, marginBottom: 8 },
  stepDesc: { fontSize: 14, color: C.onSurfaceVariant, lineHeight: 22 },

  startGuidedWrap: { paddingTop: 24, borderTopWidth: 1, borderTopColor: 'rgba(172,173,173,0.1)', marginTop: 40 },
  startGuidedBtn: {
    backgroundColor: C.primary, flexDirection: 'row', alignItems: 'center', justifyContent: 'center',
    gap: 12, paddingVertical: 16, borderRadius: 12,
  },
  startGuidedText: { color: C.onPrimary, fontSize: 18, fontWeight: 'bold' },

  masterclassBox: {
    backgroundColor: 'rgba(255,199,145,0.3)', marginHorizontal: 24, padding: 32,
    borderRadius: 24, gap: 24,
    // Note: the original design had row structure on desktop, column on mobile
  },
  mcLeft: { flexDirection: 'row', alignItems: 'center', gap: 24 },
  mcIconWrap: {
    width: 80, height: 80, backgroundColor: C.surfaceContainerLowest, borderRadius: 16,
    alignItems: 'center', justifyContent: 'center', shadowColor: '#000', shadowOpacity: 0.05, shadowRadius: 10,
  },
  mcTexts: { flex: 1 },
  mcTitle: { fontSize: 20, fontWeight: 'bold', color: C.onSecondaryContainer },
  mcDesc: { fontSize: 14, color: C.onSecondaryContainer, opacity: 0.8 },
  mcBtn: {
    backgroundColor: C.surfaceContainerLowest, paddingVertical: 12, paddingHorizontal: 32,
    borderRadius: 24, alignItems: 'center', marginTop: 16
  },
  mcBtnText: { color: C.secondary, fontSize: 16, fontWeight: 'bold' },
});
