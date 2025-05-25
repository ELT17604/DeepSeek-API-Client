// This file implements API key encryption and decryption functionality.

function getEncryptionKey() {
    const machineId = navigator.userAgent; // Using user agent as a simple machine identifier
    const keyMaterial = `deepseek-client-${machineId}-salt-v1`;
    const encoder = new TextEncoder();
    const data = encoder.encode(keyMaterial);
    
    return crypto.subtle.digest('SHA-256', data).then(hash => {
        return btoa(String.fromCharCode(...new Uint8Array(hash))).replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/, '');
    });
}

async function encryptApiKey(apiKey) {
    if (!apiKey) return null;

    const key = await getEncryptionKey();
    const encoder = new TextEncoder();
    const data = encoder.encode(apiKey);
    
    const cryptoKey = await crypto.subtle.importKey('raw', encoder.encode(key), { name: 'AES-GCM' }, false, ['encrypt']);
    const iv = crypto.getRandomValues(new Uint8Array(12)); // Initialization vector

    const encrypted = await crypto.subtle.encrypt({ name: 'AES-GCM', iv: iv }, cryptoKey, data);
    const encryptedArray = new Uint8Array(encrypted);
    
    return {
        iv: btoa(String.fromCharCode(...iv)),
        data: btoa(String.fromCharCode(...encryptedArray))
    };
}

async function decryptApiKey(encryptedApiKey) {
    if (!encryptedApiKey || !encryptedApiKey.iv || !encryptedApiKey.data) return null;

    const key = await getEncryptionKey();
    const iv = new Uint8Array(atob(encryptedApiKey.iv).split('').map(c => c.charCodeAt(0)));
    const data = new Uint8Array(atob(encryptedApiKey.data).split('').map(c => c.charCodeAt(0)));

    const cryptoKey = await crypto.subtle.importKey('raw', new TextEncoder().encode(key), { name: 'AES-GCM' }, false, ['decrypt']);

    try {
        const decrypted = await crypto.subtle.decrypt({ name: 'AES-GCM', iv: iv }, cryptoKey, data);
        return new TextDecoder().decode(decrypted);
    } catch (e) {
        console.error('Decryption failed:', e);
        return null;
    }
}