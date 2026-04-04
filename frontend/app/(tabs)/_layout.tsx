import { Tabs } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';

const TAB_COLORS = {
  active: '#006b1b',
  inactive: '#767777',
  barBg: '#ffffff',
  border: 'rgba(172,173,173,0.15)',
};

export default function TabsLayout() {
  return (
    <Tabs
      screenOptions={{
        headerShown: false,
        tabBarActiveTintColor: TAB_COLORS.active,
        tabBarInactiveTintColor: TAB_COLORS.inactive,
        tabBarStyle: {
          backgroundColor: TAB_COLORS.barBg,
          borderTopColor: TAB_COLORS.border,
          borderTopWidth: 1,
          paddingBottom: 6,
          paddingTop: 6,
          height: 64,
          shadowColor: '#2d2f2f',
          shadowOffset: { width: 0, height: -12 },
          shadowOpacity: 0.06,
          shadowRadius: 32,
          elevation: 8,
        },
        tabBarLabelStyle: { fontSize: 10, fontWeight: '600', letterSpacing: 0.3 },
      }}
    >
      <Tabs.Screen name="home" options={{ title: 'Home', tabBarIcon: ({ color, size }) => <Ionicons name="home" size={size} color={color} /> }} />
      <Tabs.Screen name="fridge" options={{ title: 'Fridge', tabBarIcon: ({ color, size }) => <Ionicons name="basket" size={size} color={color} /> }} />
      <Tabs.Screen name="generate" options={{ title: 'Scanner', tabBarIcon: ({ color, size }) => <Ionicons name="scan" size={size} color={color} /> }} />
      <Tabs.Screen name="favorites" options={{ title: 'Favorites', tabBarIcon: ({ color, size }) => <Ionicons name="heart" size={size} color={color} /> }} />
      <Tabs.Screen name="profile" options={{ title: 'Settings', tabBarIcon: ({ color, size }) => <Ionicons name="settings" size={size} color={color} /> }} />
    </Tabs>
  );
}
