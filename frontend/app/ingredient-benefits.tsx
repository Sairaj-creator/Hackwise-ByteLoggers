import React from 'react';
import { View, Text, StyleSheet, ScrollView, Image, TouchableOpacity, SafeAreaView, Platform } from 'react-native';
import { useRouter } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';

const C = {
  surface: '#f6f6f6',
  onSurface: '#2d2f2f',
  primary: '#006b1b',
  onPrimary: '#d1ffc8',
  secondary: '#874e00',
  onSurfaceVariant: '#5a5c5c',
  tertiary: '#3c6600',
  tertiaryContainer: '#c1fd7c',
  onTertiaryContainer: '#396100',
  surfaceContainerLowest: '#ffffff',
  surfaceContainerLow: '#f0f1f1',
  surfaceContainer: '#e7e8e8',
  secondaryContainer: '#ffc791',
  onSecondaryContainer: '#6a3c00',
  primaryContainer: '#91f78e',
  onPrimaryContainer: '#005e17',
  outlineVariant: '#acadad',
};

export default function IngredientBenefitsScreen() {
  const router = useRouter();

  return (
    <SafeAreaView style={styles.safeArea}>
      <View style={styles.appBar}>
        <TouchableOpacity style={styles.iconBtn} onPress={() => router.back()}>
          <Ionicons name="arrow-back" size={24} color={C.primary} />
        </TouchableOpacity>
        <Text style={styles.appBarTitle}>Ingredia</Text>
        <TouchableOpacity style={styles.iconBtn}>
          <Ionicons name="bookmark-outline" size={24} color={C.primary} />
        </TouchableOpacity>
      </View>

      <ScrollView contentContainerStyle={styles.contentWrap}>
        {/* Editorial Header */}
        <View style={styles.headerSection}>
          <Text style={styles.dailyWisdomLabel}>DAILY WISDOM</Text>
          <Text style={styles.heroHeadline}>
            The Digital Sous-Chef's Guide to <Text style={styles.heroHeadlineItalic}>Vitality</Text>
          </Text>
          <Text style={styles.heroSubhead}>
            Deepen your culinary intelligence. Explore the molecular magic hidden within your pantry and how these essentials nourish your body and soul.
          </Text>
          <View style={styles.identifiedBadgeWrap}>
            <View style={styles.identifiedBadge}>
              <Ionicons name="sparkles" size={16} color={C.onTertiaryContainer} />
              <Text style={styles.identifiedBadgeText}>12 New Ingredients Identified</Text>
            </View>
          </View>
        </View>

        <View style={styles.grid}>
          {/* Tuscan Kale */}
          <View style={[styles.card, styles.kaleCard]}>
            <Image
              source={{ uri: 'https://lh3.googleusercontent.com/aida-public/AB6AXuC-uOvThHMxSf1f41zCxzO-g65IBkBICf_v-qthgUIfSPb-H1GoRkR65ksFQ49QlQ-2_Fb4elr6Fod7rQ2WJTNZSCJ8I6-g2hJKj0RMtv6etkJIyd3sD3XtfxjHaUal7a-SMc3O6j8C2OwhiscHJDLi11AyObL9E93wcXIkQkIhqd4cbKG2XhQQ_O3VzVc51EASFka5X156Z3sVp4X04rE89BvCmrrRHQHvRWj7qjF_hGpbe4YTIudGlUeXhmOTj8PJbVDYQlVLslmW' }}
              style={styles.cardBgImg}
            />
            <View style={styles.overlay} />
            <View style={styles.kaleContent}>
              <View style={styles.superfoodBadge}>
                <Text style={styles.superfoodBadgeText}>SUPERFOOD</Text>
              </View>
              <Text style={styles.whiteTitle}>Tuscan Kale</Text>
              <Text style={styles.whiteText}>Highly concentrated with Vitamin K and antioxidants, these dark leafy greens are the structural foundation of a high-performance diet.</Text>
              <View style={styles.tagRow}>
                <View style={styles.whiteTag}><Text style={styles.whiteTagText}>High in Vitamin K</Text></View>
                <View style={styles.whiteTag}><Text style={styles.whiteTagText}>Iron Rich</Text></View>
              </View>
            </View>
          </View>

          {/* Avocado */}
          <View style={[styles.card, { backgroundColor: C.surfaceContainerLow }]}>
            <Image
              source={{ uri: 'https://lh3.googleusercontent.com/aida-public/AB6AXuBjImlweIFt2VSJA1PIw55Hrhzz_dZQlDyr-k8nHGWyEi66ug-Xv4PzL6zOIYThlw6FIp9QT-PWcM3rTNC0KwseNyL2jKjk8KUgo4y4q1tnu8NNB1AizLHaLcu4Gju_5Jtu5exDPfTFCb8Wvgk1jFUAOte0UemjIDZQX09mlvZsqST6nuZFtNl5JuvWPn_hGop94lZnVxCKmhtpVzX_1WyO8xTNX380BbGflXKC9QDjXSmrIB_jWSdUhy_GI0202PU-jfZ3FKsj-y6z' }}
              style={styles.avocadoImg}
            />
            <View style={styles.avocadoContent}>
              <Text style={styles.smLabelOrange}>HEALTHY FATS</Text>
              <Text style={styles.mdTitleText}>Haas Avocado</Text>
              <Text style={styles.smBodyText}>The "Butter of Nature" provides essential monounsaturated fats that optimize brain function and nutrient absorption.</Text>
              
              <View style={styles.cardFooter}>
                <Text style={styles.footerActionText}>Read Molecular Profile</Text>
                <Ionicons name="arrow-forward" size={16} color={C.primary} />
              </View>
            </View>
          </View>

          {/* Salmon */}
          <View style={[styles.card, { backgroundColor: C.surfaceContainerLowest }]}>
            <View style={styles.salmonContent}>
               <Text style={styles.smLabelGreen}>ESSENTIAL PROTEIN</Text>
               <Text style={[styles.mdTitleText, { fontSize: 28, marginBottom: 16 }]}>Wild-Caught Atlantic Salmon</Text>
               <Text style={[styles.smBodyText, { marginBottom: 24, fontSize: 16 }]}>
                 Rich in Omega-3 fatty acids, this premium protein source is vital for cardiovascular health and cognitive clarity.
               </Text>
               <View style={styles.statsRow}>
                 <View style={styles.statBox}>
                   <Text style={styles.statValGreen}>25g</Text>
                   <Text style={styles.statLabel}>Protein / 100g</Text>
                 </View>
                 <View style={styles.statBox}>
                   <Text style={styles.statValOrange}>2.3g</Text>
                   <Text style={styles.statLabel}>Omega-3s</Text>
                 </View>
               </View>
            </View>
            <Image
              source={{ uri: 'https://lh3.googleusercontent.com/aida-public/AB6AXuAZksoIx_Y17C4Fv5_M65oxyHp4OK9YOzdKtyarJmtS6NF-v4hvAE7XG8Ow8OQnY-05GiX2N-1eWwgknoH0rtLZ5o2RVnp9_CW346ZhUIg2bW3hM94lPllDO1wme8WdIZb557Z1S-kZG0gMpo9tg87VIN4gVVMy9Zk5gQ_e_wwip6feRcix6tRbui02T6RSkaVhOMCNTEJsK8IwOFf2HbbPGcGMpOlbG9LIyEEaikpjFk87jFnVNRL_6IgkNp6AjGX3-MydFKmZ1EVQ' }}
              style={styles.salmonImg}
            />
          </View>

          {/* Small Cards */}
          <View style={styles.smallCardRow}>
            {/* Turmeric */}
            <View style={[styles.smallCard, { backgroundColor: 'rgba(255,199,145,0.2)' }]}>
              <View style={styles.smallCardImgWrap}>
                <Image
                  source={{ uri: 'https://lh3.googleusercontent.com/aida-public/AB6AXuAQvKxOGcE3x6853DhV5yeS7U_t9iO_0LHkX1zNiTCSJud30Mz7sT6iX3KXGX_ZDUnYAxKt7MwnQGVSryaubQzU6PK8oj_3JehnR4y6ocLAdY_7vHrmHCXmI7T5Xz8_gJvO8HcV4YPd0yUyLBfT_I7p2JSA_17i1Zu4TNi1ksjZFOsWuUDmXjrTw36v0mdSOhXPKQ9Ll9ihOZvvt7soAtlkMmZvxxNKVUd13VaEYPhG-8SlbLQobXAknz6yeDnjbtoq81-u8gGh6p-7' }}
                  style={styles.smallCardImg}
                />
              </View>
              <View style={styles.smallCardTextWrap}>
                <Text style={styles.smallTitleOrange}>Golden Turmeric</Text>
                <Text style={styles.smallDescOrange}>The Curcumin within acts as a powerful natural anti-inflammatory agent.</Text>
              </View>
            </View>

            {/* Blueberries */}
            <View style={[styles.smallCard, { backgroundColor: 'rgba(145,247,142,0.2)' }]}>
              <View style={styles.smallCardImgWrap}>
                <Image
                  source={{ uri: 'https://lh3.googleusercontent.com/aida-public/AB6AXuDfYeYHbqTmje-yxT2yOydL_tFADBLTmevxNkLEoSew_-40gQwxOH-q9zpSHMuE7PvfvB0PYLVZLXL7j8olVe7Iim0SwU0--mSgQQdNet07ueahYBQHFFY9O1xadBN9o_fz1c4MKPzvNR0Qarau-WPB838aUp64fuIYTq7WW8vez7VqYQbvcoqSHx9mjsN09gm8w1GYhhnIChmsf8myD6GWqQAfn5OsV84_-p0GMZKVfSdgCN3JUsRPq8pdpm6bLOBOBaBGDR-Wlxi8' }}
                  style={styles.smallCardImg}
                />
              </View>
              <View style={styles.smallCardTextWrap}>
                <Text style={styles.smallTitleGreen}>Wild Blueberries</Text>
                <Text style={styles.smallDescGreen}>Dense with anthocyanins that support long-term memory and cellular repair.</Text>
              </View>
            </View>
          </View>
        </View>

      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safeArea: { flex: 1, backgroundColor: C.surface },
  appBar: {
    flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center',
    paddingHorizontal: 24, paddingVertical: 16, backgroundColor: C.surface,
    borderBottomWidth: 1, borderBottomColor: 'rgba(0,0,0,0.05)',
  },
  appBarTitle: { fontSize: 20, fontWeight: 'bold', fontStyle: 'italic', color: C.primary, letterSpacing: -0.5 },
  iconBtn: { padding: 4 },

  contentWrap: { paddingHorizontal: 24, paddingTop: 32, paddingBottom: 100 },

  headerSection: { marginBottom: 32 },
  dailyWisdomLabel: { color: C.secondary, fontSize: 12, fontWeight: 'bold', letterSpacing: 2, marginBottom: 12 },
  heroHeadline: { fontSize: 36, fontWeight: '900', color: C.onSurface, lineHeight: 40, marginBottom: 16 },
  heroHeadlineItalic: { fontStyle: 'italic', color: C.primary },
  heroSubhead: { fontSize: 16, color: C.onSurfaceVariant, lineHeight: 24, marginBottom: 24 },
  identifiedBadgeWrap: { flexDirection: 'row' },
  identifiedBadge: {
    flexDirection: 'row', alignItems: 'center', backgroundColor: C.tertiaryContainer,
    paddingHorizontal: 16, paddingVertical: 12, borderRadius: 12, gap: 8,
  },
  identifiedBadgeText: { fontSize: 12, fontWeight: 'bold', color: C.onTertiaryContainer },

  grid: { gap: 24 },

  card: { borderRadius: 24, overflow: 'hidden' },
  kaleCard: { height: 400, position: 'relative' },
  cardBgImg: { width: '100%', height: '100%', position: 'absolute' },
  overlay: { ...StyleSheet.absoluteFillObject, backgroundColor: 'rgba(0,0,0,0.5)' },
  kaleContent: { position: 'absolute', bottom: 0, left: 0, right: 0, padding: 24 },
  superfoodBadge: { backgroundColor: C.primary, alignSelf: 'flex-start', paddingHorizontal: 12, paddingVertical: 6, borderRadius: 16, marginBottom: 12 },
  superfoodBadgeText: { color: C.onPrimary, fontSize: 10, fontWeight: 'bold', letterSpacing: 1 },
  whiteTitle: { color: '#fff', fontSize: 32, fontWeight: 'bold', marginBottom: 8 },
  whiteText: { color: 'rgba(255,255,255,0.8)', fontSize: 16, lineHeight: 24, marginBottom: 16 },
  tagRow: { flexDirection: 'row', gap: 12, flexWrap: 'wrap' },
  whiteTag: { backgroundColor: 'rgba(255,255,255,0.2)', paddingHorizontal: 16, paddingVertical: 8, borderRadius: 16, borderWidth: 1, borderColor: 'rgba(255,255,255,0.1)' },
  whiteTagText: { color: '#fff', fontSize: 12, fontWeight: 'bold' },

  avocadoImg: { width: '100%', height: 200 },
  avocadoContent: { padding: 24 },
  smLabelOrange: { color: C.secondary, fontSize: 10, fontWeight: 'bold', letterSpacing: 1, marginBottom: 8 },
  mdTitleText: { fontSize: 24, fontWeight: 'bold', color: C.onSurface, marginBottom: 12 },
  smBodyText: { fontSize: 14, color: C.onSurfaceVariant, lineHeight: 22, marginBottom: 24 },
  cardFooter: { flexDirection: 'row', alignItems: 'center', borderTopWidth: 1, borderTopColor: 'rgba(0,0,0,0.05)', paddingTop: 16, gap: 8 },
  footerActionText: { color: C.primary, fontSize: 14, fontWeight: 'bold' },

  salmonContent: { padding: 32 },
  smLabelGreen: { color: C.tertiary, fontSize: 10, fontWeight: 'bold', letterSpacing: 1, marginBottom: 12 },
  statsRow: { flexDirection: 'row', gap: 16 },
  statBox: { backgroundColor: C.surfaceContainer, padding: 12, borderRadius: 12, flex: 1 },
  statValGreen: { color: C.primary, fontSize: 20, fontWeight: 'bold' },
  statValOrange: { color: C.secondary, fontSize: 20, fontWeight: 'bold' },
  statLabel: { color: C.onSurfaceVariant, fontSize: 10, fontWeight: 'bold', marginTop: 4 },
  salmonImg: { width: '100%', height: 250 },

  smallCardRow: { gap: 24 },
  smallCard: { flexDirection: 'row', alignItems: 'center', padding: 24, borderRadius: 24, gap: 16 },
  smallCardImgWrap: { width: 80, height: 80, borderRadius: 40, borderWidth: 3, borderColor: '#fff', overflow: 'hidden' },
  smallCardImg: { width: '100%', height: '100%' },
  smallCardTextWrap: { flex: 1 },
  smallTitleOrange: { fontSize: 18, fontWeight: 'bold', color: '#6a3c00', marginBottom: 4 },
  smallDescOrange: { fontSize: 12, color: 'rgba(106,60,0,0.8)', lineHeight: 18 },
  smallTitleGreen: { fontSize: 18, fontWeight: 'bold', color: '#005e17', marginBottom: 4 },
  smallDescGreen: { fontSize: 12, color: 'rgba(0,94,23,0.8)', lineHeight: 18 },
});
