import React from 'react';
import { motion } from 'framer-motion';
import { User, Bell, ShieldCheck, LogOut } from 'lucide-react';

function Settings({ isAuthenticated, onLogin, onLogout }) {
  return (
    <div className="space-y-6">
      <motion.div
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        className="flex flex-col md:flex-row md:items-center md:justify-between gap-4"
      >
        <div>
          <h1 className="text-3xl font-bold">Settings</h1>
          <p className="text-spotify-gray mt-1">Manage your demo account and app preferences.</p>
        </div>
      </motion.div>

      <div className="grid gap-6 md:grid-cols-2">
        <div className="bg-spotify-light rounded-2xl p-6">
          <div className="flex items-center gap-3 mb-4">
            <User size={20} className="text-spotify-green" />
            <h2 className="text-xl font-semibold">Account</h2>
          </div>
          <p className="text-spotify-gray mb-4">You are using the Harmony demo account for mood analysis and recommendations.</p>
          {isAuthenticated ? (
            <motion.button
              whileTap={{ scale: 0.98 }}
              onClick={onLogout}
              className="spotify-button"
            >
              <LogOut size={16} />
              <span className="ml-2">Disconnect Demo Session</span>
            </motion.button>
          ) : (
            <motion.button
              whileTap={{ scale: 0.98 }}
              onClick={onLogin}
              className="spotify-button"
            >
              Connect SoundCloud
            </motion.button>
          )}
        </div>

        <div className="bg-spotify-light rounded-2xl p-6">
          <div className="flex items-center gap-3 mb-4">
            <ShieldCheck size={20} className="text-spotify-green" />
            <h2 className="text-xl font-semibold">Privacy</h2>
          </div>
          <p className="text-spotify-gray">Mood detection is simulated in this demo and no facial data is stored. Your demo session remains local to this browser.</p>
        </div>
      </div>

      <div className="bg-spotify-light rounded-2xl p-6">
        <div className="flex items-center gap-3 mb-4">
          <Bell size={20} className="text-spotify-green" />
          <h2 className="text-xl font-semibold">Notifications</h2>
        </div>
        <p className="text-spotify-gray">Harmony can notify you when a new mood is detected and provide fresh song recommendations automatically.</p>
      </div>
    </div>
  );
}

export default Settings;
