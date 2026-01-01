import React from 'react';
import { motion } from 'framer-motion';
import { Link } from 'react-router-dom';
import { Home, ArrowLeft, MapPin, Phone, Mail, Linkedin, Github } from 'lucide-react';

const NotFoundPage = () => {
  return (
    <div className="min-h-screen bg-white flex items-center justify-center px-4">
      {/* Main Content */}
      <div className="text-center max-w-2xl mx-auto">
        {/* 404 Number - Tall font style */}
        <motion.div
          className="mb-8"
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
        >
          <h1 
            className="text-[200px] md:text-[280px] font-black text-[#292929] leading-none select-none tracking-tighter"
            style={{
              fontFamily: "'Arial Black', 'Helvetica Bold', sans-serif",
              fontStretch: 'condensed',
              letterSpacing: '-0.05em',
              transform: 'scaleY(1.3)',
            }}
          >
            404
          </h1>
        </motion.div>

        {/* Message */}
        <motion.div
          className="mb-10"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
        >
          <h2 className="text-2xl md:text-3xl font-bold text-[#292929] mb-4">
            Page Not Found
          </h2>
          <p className="text-lg text-neutral-600 max-w-md mx-auto">
            The page you're looking for doesn't exist or has been moved.
          </p>
        </motion.div>

        {/* Action Buttons */}
        <motion.div
          className="flex flex-col sm:flex-row items-center justify-center gap-4 mb-12"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.3 }}
        >
          <Link to="/">
            <button className="flex items-center gap-2 px-8 py-4 bg-[#292929] text-white font-semibold rounded-xl hover:bg-[#444] transition-colors">
              <Home className="w-5 h-5" />
              Return Home
            </button>
          </Link>

          <button
            onClick={() => window.history.back()}
            className="flex items-center gap-2 px-6 py-4 border-2 border-[#292929] text-[#292929] font-medium rounded-xl hover:bg-neutral-100 transition-colors"
          >
            <ArrowLeft className="w-5 h-5" />
            Go Back
          </button>
        </motion.div>

        {/* Divider */}
        <div className="w-24 h-0.5 bg-neutral-200 mx-auto mb-8" />

        {/* Contact Information */}
        <motion.div
          className="space-y-4 text-neutral-600"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.4 }}
        >
          <p className="text-sm font-medium text-neutral-400 uppercase tracking-wide mb-4">
            Contact Us
          </p>

          {/* Location */}
          <div className="flex items-center justify-center gap-2">
            <MapPin className="w-4 h-4 text-neutral-400" />
            <span className="text-sm">Lovely Professional University, Jalandhar</span>
          </div>

          {/* Phone */}
          <div className="flex items-center justify-center gap-2">
            <Phone className="w-4 h-4 text-neutral-400" />
            <a href="tel:1234567890" className="text-sm hover:text-[#292929] transition-colors">
              1234567890
            </a>
          </div>

          {/* Email */}
          <div className="flex items-center justify-center gap-2">
            <Mail className="w-4 h-4 text-neutral-400" />
            <a href="mailto:partapbhanu516@gmail.com" className="text-sm hover:text-[#292929] transition-colors">
              partapbhanu516@gmail.com
            </a>
          </div>

          {/* Social Links */}
          <div className="flex items-center justify-center gap-4 pt-4">
            <a
              href="https://www.linkedin.com/in/bhanu-partap-a49084274/"
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center gap-2 px-4 py-2 border border-neutral-200 rounded-lg hover:border-[#0077b5] hover:text-[#0077b5] transition-colors"
            >
              <Linkedin className="w-4 h-4" />
              <span className="text-sm font-medium">LinkedIn</span>
            </a>
            <a
              href="https://github.com/Bhanu-partap-13"
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center gap-2 px-4 py-2 border border-neutral-200 rounded-lg hover:border-[#292929] hover:text-[#292929] transition-colors"
            >
              <Github className="w-4 h-4" />
              <span className="text-sm font-medium">GitHub</span>
            </a>
          </div>
        </motion.div>
      </div>
    </div>
  );
};

export default NotFoundPage;
