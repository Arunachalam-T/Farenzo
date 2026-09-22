const https = require('https');
const mongoose = require('mongoose');
const dns = require('dns');

// ✅ Fix: Use Google's public DNS (8.8.8.8) instead of college network DNS
// College WiFi blocks MongoDB's SRV record lookups — Google DNS does not
dns.setServers(['8.8.8.8', '8.8.4.4']);

// Resolve DNS via Google's DNS-over-HTTPS (port 443 - never blocked)
async function resolveDoH(name, type = 'SRV') {
  return new Promise((resolve, reject) => {
    const url = `https://dns.google/resolve?name=${encodeURIComponent(name)}&type=${type}`;
    https.get(url, (res) => {
      let data = '';
      res.on('data', chunk => data += chunk);
      res.on('end', () => {
        try {
          const result = JSON.parse(data);
          resolve(result.Answer || []);
        } catch (e) { reject(e); }
      });
    }).on('error', reject);
  });
}

// Convert mongodb+srv:// → mongodb:// using DoH
async function buildDirectURI(srvUri) {
  const match = srvUri.match(/mongodb\+srv:\/\/([^:]+):([^@]+)@([^\/\?]+)(\/[^\?]*)?(.*)?/);
  if (!match) return srvUri;

  const [, user, pass, hostname, dbPath] = match;
  const db = (dbPath || '/farenzo').replace('/', '') || 'farenzo';

  try {
    console.log('🔍 Resolving MongoDB SRV via DNS-over-HTTPS (Google DoH)...');

    const srvRecords = await resolveDoH(`_mongodb._tcp.${hostname}`);
    if (!srvRecords.length) throw new Error('No SRV records found');

    const txtRecords = await resolveDoH(hostname, 'TXT');

    const hosts = srvRecords.map(r => {
      const parts = r.data.trim().split(/\s+/);
      const port = parts[2];
      const target = parts[3].replace(/\.$/, '');
      return `${target}:${port}`;
    }).join(',');

    let options = 'ssl=true&authSource=admin';
    for (const txt of txtRecords) {
      if (txt.data && txt.data.includes('replicaSet')) {
        options = txt.data.replace(/"/g, '');
        break;
      }
    }

    const directUri = `mongodb://${user}:${pass}@${hosts}/${db}?${options}&ssl=true&authSource=admin`;
    console.log(`✅ SRV resolved to ${srvRecords.length} host(s). Connecting...`);
    return directUri;

  } catch (e) {
    console.log(`⚠️ DoH resolution failed (${e.message}), trying original URI...`);
    return srvUri;
  }
}

const connectDB = async () => {
  try {
    let uri = process.env.MONGO_URI;

    if (uri && uri.startsWith('mongodb+srv://')) {
      uri = await buildDirectURI(uri);
    }

    const conn = await mongoose.connect(uri);
    console.log(`✅ MongoDB Connected: ${conn.connection.host}`);
  } catch (error) {
    console.error(`❌ Error connecting to MongoDB: ${error.message}`);
    process.exit(1);
  }
};

module.exports = connectDB;
