import React, { useEffect, useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';

// Floating particles for subtle background effect
const particles = Array.from({ length: 20 }, () => ({
  left: Math.random() * 100,
  top: Math.random() * 100,
  duration: 3 + Math.random() * 4,
  delay: Math.random() * 2,
  size: 2 + Math.random() * 3,
}));

// Namaste texts in different languages
const namasteTexts = [
  { text: 'Namaste', lang: 'english', className: 'font-display' },
  { text: 'नमस्ते', lang: 'hindi', className: 'font-hindi' },
  { text: 'نمستے', lang: 'urdu', className: 'font-urdu' },
];

const LoadingScreen = () => {
  const [currentTextIndex, setCurrentTextIndex] = useState(0);

  useEffect(() => {
    const interval = setInterval(() => {
      setCurrentTextIndex((prev) => (prev + 1) % namasteTexts.length);
    }, 1200);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="fixed inset-0 bg-[#0a0a0a] flex flex-col items-center justify-center z-50 overflow-hidden">
      {/* Floating Particles */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        {particles.map((particle, i) => (
          <motion.div
            key={i}
            className="absolute rounded-full bg-white/20"
            style={{
              left: `${particle.left}%`,
              top: `${particle.top}%`,
              width: particle.size,
              height: particle.size,
            }}
            animate={{
              y: [0, -40, 0],
              opacity: [0.1, 0.3, 0.1],
            }}
            transition={{
              duration: particle.duration,
              repeat: Infinity,
              delay: particle.delay,
            }}
          />
        ))}
      </div>

      {/* Main Content */}
      <div className="relative z-10 flex flex-col items-center justify-center">
        {/* Namaste Text Animation */}
        <div className="relative h-40 flex items-center justify-center">
          <AnimatePresence mode="wait">
            <motion.div
              key={currentTextIndex}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20 }}
              transition={{ duration: 0.4, ease: 'easeOut' }}
              className="text-center"
            >
              <h1
                className={`text-7xl md:text-8xl lg:text-9xl text-white font-bold ${namasteTexts[currentTextIndex].className}`}
                style={{
                  direction: namasteTexts[currentTextIndex].lang === 'urdu' ? 'rtl' : 'ltr',
                }}
              >
                {namasteTexts[currentTextIndex].text}
              </h1>
              <motion.p
                className="text-white/40 text-xs mt-4 tracking-[0.3em] uppercase"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                transition={{ delay: 0.2 }}
              >
                {namasteTexts[currentTextIndex].lang}
              </motion.p>
            </motion.div>
          </AnimatePresence>
        </div>

        {/* Loading Indicator */}
        <motion.div
          className="mt-16 flex items-center gap-3"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.5 }}
        >
          <motion.div className="flex gap-1.5">
            {[...Array(3)].map((_, i) => (
              <motion.span
                key={i}
                className="w-2 h-2 bg-white/60 rounded-full"
                animate={{
                  scale: [1, 1.3, 1],
                  opacity: [0.4, 1, 0.4],
                }}
                transition={{
                  duration: 1.2,
                  repeat: Infinity,
                  delay: i * 0.2,
                }}
              />
            ))}
          </motion.div>
          <span className="text-white/50 text-sm tracking-wider font-light">
            Loading AgriStack
          </span>
        </motion.div>
      </div>

      {/* Minimal corner accents */}
      <div className="absolute top-8 left-8 w-8 h-8 border-l border-t border-white/10" />
      <div className="absolute top-8 right-8 w-8 h-8 border-r border-t border-white/10" />
      <div className="absolute bottom-8 left-8 w-8 h-8 border-l border-b border-white/10" />
      <div className="absolute bottom-8 right-8 w-8 h-8 border-r border-b border-white/10" />
    </div>
  );
};

export default LoadingScreen;
