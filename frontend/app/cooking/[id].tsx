import React, { useEffect, useState, useRef, useCallback } from 'react';
import { View, Text, StyleSheet, TouchableOpacity, ScrollView, Dimensions, Alert } from 'react-native';
import { useLocalSearchParams, useRouter } from 'expo-router';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { api } from '@/services/api';
import { Colors, Spacing, Radius } from '@/constants/theme';
import { Ionicons } from '@expo/vector-icons';
import { activateKeepAwakeAsync, deactivateKeepAwake } from 'expo-keep-awake';

const { width: SCREEN_WIDTH } = Dimensions.get('window');

export default function CookingModeScreen() {
  const { id } = useLocalSearchParams<{ id: string }>();
  const insets = useSafeAreaInsets();
  const router = useRouter();
  const scrollRef = useRef<ScrollView>(null);
  const [data, setData] = useState<any>(null);
  const [currentStep, setCurrentStep] = useState(0);
  const [timer, setTimer] = useState<number | null>(null);
  const [timerRunning, setTimerRunning] = useState(false);
  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null);

  useEffect(() => {
    activateKeepAwakeAsync();
    (async () => {
      try {
        const res = await api.getCookingData(id!);
        setData(res);
      } catch {}
    })();
    return () => { deactivateKeepAwake(); if (timerRef.current) clearInterval(timerRef.current); };
  }, [id]);

  const steps = data?.steps || [];
  const step = steps[currentStep];

  const goToStep = useCallback((idx: number) => {
    setCurrentStep(idx);
    scrollRef.current?.scrollTo({ x: idx * SCREEN_WIDTH, animated: true });
    if (timerRef.current) { clearInterval(timerRef.current); timerRef.current = null; }
    setTimerRunning(false);
    const s = steps[idx];
    setTimer(s?.timer_seconds || null);
  }, [steps]);

  const startTimer = () => {
    if (timer === null || timer <= 0) return;
    setTimerRunning(true);
    timerRef.current = setInterval(() => {
      setTimer(prev => {
        if (prev !== null && prev <= 1) {
          clearInterval(timerRef.current!);
          timerRef.current = null;
          setTimerRunning(false);
          Alert.alert('Timer Done!', 'This step\'s timer has finished.');
          return 0;
        }
        return prev !== null ? prev - 1 : null;
      });
    }, 1000);
  };

  const pauseTimer = () => {
    if (timerRef.current) { clearInterval(timerRef.current); timerRef.current = null; }
    setTimerRunning(false);
  };

  const handleDoneCooking = async () => {
    try {
      await api.doneCooking(id!);
      Alert.alert('Great job!', 'Recipe marked as cooked.', [{ text: 'OK', onPress: () => router.back() }]);
    } catch {
      router.back();
    }
  };

  const formatTime = (seconds: number) => {
    const m = Math.floor(seconds / 60);
    const s = seconds % 60;
    return `${m.toString().padStart(2, '0')}:${s.toString().padStart(2, '0')}`;
  };

  if (!data) {
    return <View style={styles.container}><Text style={styles.loadingText}>Loading...</Text></View>;
  }

  return (
    <View style={[styles.container, { paddingTop: insets.top }]}>
      {/* Header */}
      <View style={styles.header}>
        <TouchableOpacity testID="cooking-close-btn" onPress={() => router.back()} style={styles.closeBtn}>
          <Ionicons name="close" size={28} color={Colors.textCooking} />
        </TouchableOpacity>
        <View style={styles.headerCenter}>
          <Text style={styles.headerTitle} numberOfLines={1}>{data.title || "Cooking Mode"}</Text>
          <Text style={styles.stepIndicator}>Step {currentStep + 1} of {steps.length}</Text>
        </View>
        <View style={{ width: 44 }} />
      </View>

      {/* Progress */}
      <View style={styles.progressRow}>
        {steps.map((_: any, i: number) => (
          <View key={i} style={[styles.progressDot, i <= currentStep && styles.progressDotActive]} />
        ))}
      </View>

      {/* Steps */}
      <ScrollView
        ref={scrollRef}
        horizontal
        pagingEnabled
        showsHorizontalScrollIndicator={false}
        scrollEnabled={false}
        contentContainerStyle={{ width: SCREEN_WIDTH * steps.length }}
      >
        {steps.map((s: any, i: number) => (
          <View key={i} style={[styles.stepContainer, { width: SCREEN_WIDTH }]}>
            <ScrollView contentContainerStyle={styles.stepScroll}>
              <View style={styles.stepNumberCircle}>
                <Text style={styles.stepNumberText}>{s.step || i + 1}</Text>
              </View>
              <Text style={styles.stepInstruction}>{s.instruction}</Text>

              {s.timer_seconds && i === currentStep && (
                <View style={styles.timerSection}>
                  <Text style={styles.timerDisplay}>{formatTime(timer ?? s.timer_seconds)}</Text>
                  <View style={styles.timerControls}>
                    {!timerRunning ? (
                      <TouchableOpacity testID="cooking-timer-start" style={styles.timerBtn} onPress={startTimer}>
                        <Ionicons name="play" size={24} color={Colors.textInverse} />
                        <Text style={styles.timerBtnText}>Start</Text>
                      </TouchableOpacity>
                    ) : (
                      <TouchableOpacity testID="cooking-timer-pause" style={[styles.timerBtn, styles.timerBtnPause]} onPress={pauseTimer}>
                        <Ionicons name="pause" size={24} color={Colors.textInverse} />
                        <Text style={styles.timerBtnText}>Pause</Text>
                      </TouchableOpacity>
                    )}
                    <TouchableOpacity testID="cooking-timer-reset" style={styles.timerResetBtn} onPress={() => { pauseTimer(); setTimer(s.timer_seconds); }}>
                      <Ionicons name="refresh" size={20} color={Colors.textCooking} />
                    </TouchableOpacity>
                  </View>
                </View>
              )}
            </ScrollView>
          </View>
        ))}
      </ScrollView>

      {/* Navigation */}
      <View style={[styles.navRow, { paddingBottom: insets.bottom + Spacing.md }]}>
        <TouchableOpacity
          testID="cooking-prev-btn"
          style={[styles.navBtn, currentStep === 0 && styles.navBtnDisabled]}
          onPress={() => currentStep > 0 && goToStep(currentStep - 1)}
          disabled={currentStep === 0}
        >
          <Ionicons name="chevron-back" size={24} color={currentStep === 0 ? Colors.expired : Colors.textCooking} />
          <Text style={[styles.navBtnText, currentStep === 0 && { color: Colors.expired }]}>Previous</Text>
        </TouchableOpacity>

        {currentStep < steps.length - 1 ? (
          <TouchableOpacity testID="cooking-next-btn" style={styles.nextBtn} onPress={() => goToStep(currentStep + 1)}>
            <Text style={styles.nextBtnText}>Next</Text>
            <Ionicons name="chevron-forward" size={24} color={Colors.textInverse} />
          </TouchableOpacity>
        ) : (
          <TouchableOpacity testID="cooking-done-btn" style={styles.doneBtn} onPress={handleDoneCooking}>
            <Ionicons name="checkmark-circle" size={24} color={Colors.textInverse} />
            <Text style={styles.doneBtnText}>Done Cooking</Text>
          </TouchableOpacity>
        )}
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: Colors.cookingBg },
  loadingText: { color: Colors.textCooking, fontSize: 16, textAlign: 'center', marginTop: 100 },
  header: { flexDirection: 'row', alignItems: 'center', paddingHorizontal: Spacing.md, paddingVertical: Spacing.sm },
  closeBtn: { width: 44, height: 44, alignItems: 'center', justifyContent: 'center' },
  headerCenter: { flex: 1, alignItems: 'center' },
  headerTitle: { fontSize: 16, fontWeight: '700', color: Colors.textCooking },
  stepIndicator: { fontSize: 13, color: Colors.expired, marginTop: 2 },
  progressRow: { flexDirection: 'row', justifyContent: 'center', gap: 6, paddingVertical: Spacing.sm },
  progressDot: { width: 8, height: 8, borderRadius: 4, backgroundColor: 'rgba(255,255,255,0.2)' },
  progressDotActive: { backgroundColor: Colors.orange, width: 20 },
  stepContainer: { justifyContent: 'center', alignItems: 'center' },
  stepScroll: { paddingHorizontal: Spacing.xl, paddingTop: Spacing.xl, alignItems: 'center' },
  stepNumberCircle: { width: 56, height: 56, borderRadius: 28, backgroundColor: Colors.orange, alignItems: 'center', justifyContent: 'center', marginBottom: Spacing.lg },
  stepNumberText: { fontSize: 24, fontWeight: '900', color: Colors.textInverse },
  stepInstruction: { fontSize: 22, fontWeight: '600', color: Colors.textCooking, textAlign: 'center', lineHeight: 32 },
  timerSection: { marginTop: Spacing.xl, alignItems: 'center' },
  timerDisplay: { fontSize: 56, fontWeight: '900', color: Colors.orange, fontVariant: ['tabular-nums'] },
  timerControls: { flexDirection: 'row', alignItems: 'center', gap: Spacing.md, marginTop: Spacing.md },
  timerBtn: { flexDirection: 'row', alignItems: 'center', gap: 8, backgroundColor: Colors.fresh, paddingHorizontal: 24, paddingVertical: 12, borderRadius: Radius.full },
  timerBtnPause: { backgroundColor: Colors.amber },
  timerBtnText: { color: Colors.textInverse, fontSize: 16, fontWeight: '700' },
  timerResetBtn: { width: 44, height: 44, borderRadius: 22, borderWidth: 1, borderColor: 'rgba(255,255,255,0.3)', alignItems: 'center', justifyContent: 'center' },
  navRow: { flexDirection: 'row', justifyContent: 'space-between', paddingHorizontal: Spacing.lg, paddingTop: Spacing.md },
  navBtn: { flexDirection: 'row', alignItems: 'center', gap: 4, paddingVertical: 12, paddingHorizontal: 16 },
  navBtnDisabled: { opacity: 0.4 },
  navBtnText: { color: Colors.textCooking, fontSize: 16, fontWeight: '600' },
  nextBtn: { flexDirection: 'row', alignItems: 'center', gap: 4, backgroundColor: Colors.orange, paddingVertical: 14, paddingHorizontal: 24, borderRadius: Radius.full },
  nextBtnText: { color: Colors.textInverse, fontSize: 16, fontWeight: '700' },
  doneBtn: { flexDirection: 'row', alignItems: 'center', gap: 8, backgroundColor: Colors.fresh, paddingVertical: 14, paddingHorizontal: 24, borderRadius: Radius.full },
  doneBtnText: { color: Colors.textInverse, fontSize: 16, fontWeight: '700' },
});
