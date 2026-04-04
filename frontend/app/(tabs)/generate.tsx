import React, { useState, useEffect, useCallback } from 'react';
import { View, Text, StyleSheet, TouchableOpacity, ScrollView, TextInput, ActivityIndicator, Image, Modal, Alert } from 'react-native';
import { useRouter } from 'expo-router';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { api } from '@/services/api';
import { Ionicons } from '@expo/vector-icons';

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

const CAMERA_BG = 'https://lh3.googleusercontent.com/aida-public/AB6AXuBmnYT8Y_IkvZFrt4K3bWljjoy49kb61c4FPWK_fe2B2dh8wXEXQgJg7Rg3fPkcnwOuThXjTFMeO3nCHp1eGHmZZXE-kdMiFuYeC1F8heT3icfF2wXuRHe1jAGxj4QcVMXyPWLdQUS9DeZQ9hei3_qMo3K9fPodvol9EncBhw-nwyVT6ufnV8t9Myyo9CzPGBCji0-r35blZM50_idgiH4LtX8ftuUVaWHJddNmn_Xn45dLIgKExNjU10ul6cVUvR0abyJsjGJtP3Tj';
const DEFAULT_IMG = 'https://images.unsplash.com/photo-1546069901-ba9599a7e63c?ixlib=rb-4.0.3&auto=format&fit=crop&w=800&q=80';

export default function GenerateScreen() {
  const insets = useSafeAreaInsets();
  const router = useRouter();
  const [fridgeItems, setFridgeItems] = useState<any[]>([]);
  const [selectedIngredients, setSelectedIngredients] = useState<string[]>([]);
  const [generating, setGenerating] = useState(false);
  const [recipe, setRecipe] = useState<any>(null);
  const [error, setError] = useState('');
  const [scanning, setScanning] = useState(false);
  const [showManualAdd, setShowManualAdd] = useState(false);
  const [manualText, setManualText] = useState('');

  const loadFridge = useCallback(async () => {
    try {
      const data = await api.getFridge();
      setFridgeItems(data.ingredients || []);
    } catch {}
  }, []);

  useEffect(() => { loadFridge(); }, [loadFridge]);

  const removeIngredient = (name: string) => {
    setSelectedIngredients(prev => prev.filter(n => n !== name));
  };

  const handleScanMock = () => {
    setScanning(true);
    setTimeout(() => {
      setScanning(false);
      // Pick random item not already selected
      const available = fridgeItems.filter(i => !selectedIngredients.includes(i.name));
      if (available.length > 0) {
        const randomItem = available[Math.floor(Math.random() * available.length)];
        setSelectedIngredients(prev => [...prev, randomItem.name]);
      } else {
        Alert.alert('Scan Complete', "We couldn't detect new ingredients.");
      }
    }, 1500);
  };

  const handleManualAdd = () => {
    if (manualText.trim() && !selectedIngredients.includes(manualText.trim())) {
      setSelectedIngredients(prev => [...prev, manualText.trim()]);
    }
    setManualText('');
    setShowManualAdd(false);
  };

  const handleGenerate = async () => {
    if (selectedIngredients.length === 0) { setError('Please add at least one ingredient'); return; }
    setError('');
    setGenerating(true);
    setRecipe(null);
    try {
      const data = await api.generateRecipe({
        ingredients: selectedIngredients,
        servings: 2,
        preferences: {
          cuisine: '',
          dietary: '',
          max_time_minutes: '30',
          spice_level: 'medium',
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
      <View style={[styles.container, { paddingTop: insets.top }]}>
        <View style={styles.appBar}>
          <TouchableOpacity testID="generate-back-btn" onPress={() => setRecipe(null)} style={styles.iconBtn}>
            <Ionicons name="arrow-back" size={24} color={C.onSurface} />
          </TouchableOpacity>
          <Text style={styles.appBarTitle}>Recipe Generated</Text>
          <View style={{ width: 24 }} />
        </View>
        <ScrollView contentContainerStyle={styles.resultContent}>
          <Image source={{ uri: recipe.image_url || DEFAULT_IMG }} style={styles.recipeImage} />
          <Text style={styles.recipeTitle}>{recipe.title}</Text>
          <Text style={styles.recipeDesc}>{recipe.cuisine} · {recipe.difficulty}</Text>

          <View style={styles.badgeRow}>
            <View style={styles.badge}><Ionicons name="time-outline" size={14} color={C.primary} /><Text style={styles.badgeText}>{recipe.estimated_time_minutes} min</Text></View>
            <View style={styles.badge}><Ionicons name="people-outline" size={14} color={C.primary} /><Text style={styles.badgeText}>{recipe.servings} servings</Text></View>
            <View style={styles.badge}><Ionicons name="fitness-outline" size={14} color={C.primary} /><Text style={styles.badgeText}>{recipe.difficulty}</Text></View>
          </View>

          <TouchableOpacity testID="generate-view-full-btn" style={styles.viewFullBtn} onPress={() => router.push(`/recipe/${recipe.recipe_id}`)}>
            <Text style={styles.viewFullText}>View Full Recipe</Text>
            <Ionicons name="arrow-forward" size={18} color={C.surfaceLowest} />
          </TouchableOpacity>
        </ScrollView>
      </View>
    );
  }

  return (
    <View style={[styles.container, { paddingTop: insets.top }]}>
      <View style={styles.appBar}>
        <View style={styles.appBarLeft}>
          <View style={styles.avatarBorder}>
            <Image source={{ uri: 'https://lh3.googleusercontent.com/aida-public/AB6AXuC4jSkPRkcV95Ki5NsAW6RsG3TlpVNgLcKKLjbCfUithQKc6yKLtrqXQ7ElaPH_HdWaYJJM9JK0SxDvpyVwtEnNpp37D-A_hj2XDVAFr91y8I_TQ5jRnnFM5WNctNK8N0cLk4dkciBMex3GBxT7RCzYxSopH8YdxX5wV79LiZSIse1oZ63AjGZ6Q3Tm7YTC6FNKOebjZK_RmnkzCFZlyLc8R3kqU7ht8_APzlJ4t_VJwL_CEoQzVXmmXqffu86AszGfcoEMz4eivNhP' }} style={styles.avatar} />
          </View>
          <Text style={styles.appBarBrand}>The Culinary Editorial</Text>
        </View>
        <TouchableOpacity style={styles.iconBtn}>
          <Ionicons name="settings-outline" size={24} color={C.onSurfaceVariant} />
        </TouchableOpacity>
      </View>

      <ScrollView contentContainerStyle={styles.content} keyboardShouldPersistTaps="handled">
        <View style={styles.headerBox}>
          <Text style={styles.title}>Identify Your Harvest</Text>
          <Text style={styles.subtitle}>Point your camera at fresh ingredients to unlock AI-powered recipes.</Text>
        </View>

        {error ? (
          <View style={styles.errorBox}>
            <Text style={styles.errorText}>{error}</Text>
          </View>
        ) : null}

        <View style={styles.scannerWrapper}>
          <Image source={{ uri: CAMERA_BG }} style={styles.scannerImg} />
          <View style={styles.scannerOverlay} />

          <View style={styles.scannerFrameHolder}>
            <View style={[styles.corner, styles.tl]} />
            <View style={[styles.corner, styles.tr]} />
            <View style={[styles.corner, styles.bl]} />
            <View style={[styles.corner, styles.br]} />
          </View>

          {scanning && (
            <View style={styles.scanningIndicatorBox}>
              <View style={styles.scanningDot} />
              <Text style={styles.scanningText}>Detecting Ingredients...</Text>
            </View>
          )}

          <TouchableOpacity style={styles.scannerIconBtn} onPress={handleScanMock}>
            <Ionicons name="scan-outline" size={32} color={C.onPrimary} />
          </TouchableOpacity>
        </View>

        <View style={styles.actionGrid}>
          <TouchableOpacity style={styles.primaryActionBtn} onPress={handleScanMock} disabled={scanning}>
            <Ionicons name="camera" size={20} color={C.onPrimary} />
            <Text style={styles.primaryActionText}>{scanning ? 'Scanning...' : 'Scan to add ingredients'}</Text>
          </TouchableOpacity>

          <TouchableOpacity style={styles.secondaryActionBtn} onPress={() => setShowManualAdd(true)}>
            <Ionicons name="create-outline" size={20} color={C.onSurface} />
            <Text style={styles.secondaryActionText}>Click to add manually</Text>
          </TouchableOpacity>
        </View>

        <View style={styles.detectedBox}>
          <View style={styles.detectedHeader}>
            <Text style={styles.detectedTitle}>Recently Detected</Text>
            <Text style={styles.detectedSession}>LIVE SESSION</Text>
          </View>
          
          <View style={styles.chipWrap}>
            {selectedIngredients.map(item => (
              <View key={item} style={styles.chip}>
                <Text style={styles.chipText}>{item}</Text>
                <TouchableOpacity onPress={() => removeIngredient(item)}>
                  <Ionicons name="close" size={16} color={C.onTertiaryContainer} />
                </TouchableOpacity>
              </View>
            ))}
            {selectedIngredients.length === 0 && (
              <Text style={{color: C.onSurfaceVariant, fontSize: 13, marginTop: 4}}>No ingredients detected yet.</Text>
            )}
          </View>
        </View>

        {selectedIngredients.length > 0 && (
          <TouchableOpacity testID="gen-submit-btn" style={styles.generateBtn} onPress={handleGenerate} disabled={generating}>
            {generating ? (
              <ActivityIndicator color={C.surfaceLowest} />
            ) : (
              <>
                <Ionicons name="sparkles" size={20} color={C.surfaceLowest} />
                <Text style={styles.generateText}>Generate AI Recipe</Text>
              </>
            )}
          </TouchableOpacity>
        )}
      </ScrollView>

      <Modal visible={showManualAdd} animationType="fade" transparent>
        <View style={styles.modalBg}>
          <View style={styles.modalContent}>
            <Text style={styles.modalTitle}>Add Ingredient</Text>
            <TextInput 
              style={styles.modalInput}
              value={manualText}
              onChangeText={setManualText}
              placeholder="e.g. Cherry Tomato"
              autoFocus
              onSubmitEditing={handleManualAdd}
            />
            <View style={styles.modalActions}>
              <TouchableOpacity style={styles.modalCancel} onPress={() => setShowManualAdd(false)}>
                <Text style={{color: C.onSurfaceVariant, fontWeight:'bold'}}>Cancel</Text>
              </TouchableOpacity>
              <TouchableOpacity style={styles.modalAdd} onPress={handleManualAdd}>
                <Text style={{color: C.surfaceLowest, fontWeight:'bold'}}>Add</Text>
              </TouchableOpacity>
            </View>
          </View>
        </View>
      </Modal>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: C.surface },
  appBar: {
    flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center',
    paddingHorizontal: 24, paddingVertical: 16, backgroundColor: C.surface,
    borderBottomWidth: 1, borderBottomColor: C.surfaceContainerLow,
  },
  appBarLeft: { flexDirection: 'row', alignItems: 'center', gap: 12 },
  avatarBorder: {
    width: 40, height: 40, borderRadius: 20, overflow: 'hidden', backgroundColor: C.surfaceContainerLow
  },
  avatar: { width: '100%', height: '100%' },
  appBarBrand: { fontSize: 18, fontWeight: 'bold', color: C.primary },
  appBarTitle: { fontSize: 18, fontWeight: 'bold', color: C.onSurface },
  iconBtn: { padding: 4 },
  
  content: { paddingHorizontal: 24, paddingBottom: 100 },
  headerBox: { marginTop: 16, marginBottom: 32 },
  title: { fontSize: 32, fontWeight: '900', color: C.onSurface, marginBottom: 8, letterSpacing: -0.5 },
  subtitle: { fontSize: 18, color: C.onSurfaceVariant, lineHeight: 26 },
  
  errorBox: { backgroundColor: C.criticalBg, padding: 16, borderRadius: 12, marginBottom: 16 },
  errorText: { color: C.critical, fontSize: 14, fontWeight: '600' },
  
  scannerWrapper: {
    width: '100%', aspectRatio: 3/4, borderRadius: 32, overflow: 'hidden',
    backgroundColor: C.surfaceContainerLow, position: 'relative', shadowColor: '#000',
    shadowOffset: {width: 0,height: 20}, shadowOpacity: 0.1, shadowRadius: 30, elevation: 5,
  },
  scannerImg: { width: '100%', height: '100%' },
  scannerOverlay: { ...StyleSheet.absoluteFillObject, backgroundColor: 'rgba(0,0,0,0.2)' },
  
  scannerFrameHolder: { position: 'absolute', top: 48, bottom: 48, left: 48, right: 48 },
  corner: { position: 'absolute', width: 40, height: 40, borderColor: C.primary },
  tl: { top: 0, left: 0, borderTopWidth: 4, borderLeftWidth: 4, borderTopLeftRadius: 16 },
  tr: { top: 0, right: 0, borderTopWidth: 4, borderRightWidth: 4, borderTopRightRadius: 16 },
  bl: { bottom: 0, left: 0, borderBottomWidth: 4, borderLeftWidth: 4, borderBottomLeftRadius: 16 },
  br: { bottom: 0, right: 0, borderBottomWidth: 4, borderRightWidth: 4, borderBottomRightRadius: 16 },
  
  scanningIndicatorBox: {
    position: 'absolute', top: '50%', left: '50%', transform: [{translateX: -100}, {translateY: -20}],
    backgroundColor: 'rgba(255,255,255,0.85)', paddingHorizontal: 16, paddingVertical: 8,
    borderRadius: 20, flexDirection: 'row', alignItems: 'center', gap: 8,
  },
  scanningDot: { width: 8, height: 8, borderRadius: 4, backgroundColor: C.primary },
  scanningText: { fontSize: 14, fontWeight: 'bold', color: C.onSurface },
  
  scannerIconBtn: {
    position: 'absolute', bottom: 32, left: '50%', transform: [{translateX: -32}],
    width: 64, height: 64, borderRadius: 32, backgroundColor: C.primary,
    alignItems: 'center', justifyContent: 'center', borderWidth: 4, borderColor: 'rgba(255,255,255,0.2)'
  },
  
  actionGrid: { marginTop: 32, gap: 16 },
  primaryActionBtn: {
    width: '100%', backgroundColor: C.primary, paddingVertical: 20, borderRadius: 16,
    flexDirection: 'row', alignItems: 'center', justifyContent: 'center', gap: 12,
  },
  primaryActionText: { color: C.onPrimary, fontSize: 16, fontWeight: 'bold' },
  secondaryActionBtn: {
    width: '100%', backgroundColor: C.surfaceContainerLowest, paddingVertical: 20, borderRadius: 16,
    flexDirection: 'row', alignItems: 'center', justifyContent: 'center', gap: 12,
  },
  secondaryActionText: { color: C.onSurface, fontSize: 16, fontWeight: '600' },
  
  detectedBox: { marginTop: 40, backgroundColor: C.surfaceContainerLow, borderRadius: 24, padding: 24 },
  detectedHeader: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 },
  detectedTitle: { fontSize: 18, fontWeight: 'bold', color: C.onSurface },
  detectedSession: { fontSize: 10, fontWeight: 'bold', color: C.onSurfaceVariant, letterSpacing: 1 },
  
  chipWrap: { flexDirection: 'row', flexWrap: 'wrap', gap: 8 },
  chip: { 
    backgroundColor: C.tertiaryContainer, paddingHorizontal: 16, paddingVertical: 8,
    borderRadius: 20, flexDirection: 'row', alignItems: 'center', gap: 8
  },
  chipText: { fontSize: 14, fontWeight: '600', color: C.onTertiaryContainer },

  generateBtn: {
    backgroundColor: C.onSurface, borderRadius: 16, paddingVertical: 20,
    flexDirection: 'row', alignItems: 'center', justifyContent: 'center', gap: 12, marginTop: 40
  },
  generateText: { color: C.surfaceLowest, fontSize: 16, fontWeight: 'bold' },

  // Result styling
  resultContent: { padding: 24, paddingBottom: 60 },
  recipeImage: { width: '100%', height: 260, borderRadius: 24, marginBottom: 24 },
  recipeTitle: { fontSize: 28, fontWeight: '900', color: C.onSurface, marginBottom: 8 },
  recipeDesc: { fontSize: 16, color: C.onSurfaceVariant, fontWeight: '500' },
  badgeRow: { flexDirection: 'row', gap: 12, marginTop: 20 },
  badge: { flexDirection: 'row', alignItems: 'center', gap: 6, backgroundColor: C.surfaceContainerLowest, paddingHorizontal: 14, paddingVertical: 10, borderRadius: 12, borderWidth: 1, borderColor: C.surfaceContainerHigh },
  badgeText: { fontSize: 14, color: C.onSurfaceVariant, fontWeight: '600' },
  viewFullBtn: { backgroundColor: C.primary, borderRadius: 16, paddingVertical: 20, flexDirection: 'row', alignItems: 'center', justifyContent: 'center', gap: 12, marginTop: 40 },
  viewFullText: { color: C.surfaceLowest, fontSize: 18, fontWeight: 'bold' },

  // Modal
  modalBg: { flex: 1, backgroundColor: 'rgba(0,0,0,0.5)', justifyContent: 'center', alignItems: 'center', padding: 24 },
  modalContent: { width: '100%', backgroundColor: C.surfaceLowest, borderRadius: 24, padding: 24 },
  modalTitle: { fontSize: 18, fontWeight: 'bold', color: C.onSurface, marginBottom: 16 },
  modalInput: { backgroundColor: C.surface, borderRadius: 12, padding: 16, fontSize: 16, color: C.onSurface, marginBottom: 24 },
  modalActions: { flexDirection: 'row', justifyContent: 'flex-end', gap: 16 },
  modalCancel: { padding: 12, borderRadius: 8 },
  modalAdd: { backgroundColor: C.primary, paddingHorizontal: 24, paddingVertical: 12, borderRadius: 12 },
});
