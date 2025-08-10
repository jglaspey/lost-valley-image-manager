#!/bin/bash

echo "🔐 SSH Key Setup for Digital Ocean"
echo "==================================="
echo ""

# Check if SSH key already exists
if [ -f ~/.ssh/id_rsa.pub ] || [ -f ~/.ssh/id_ed25519.pub ]; then
    echo "✅ You already have SSH keys!"
    echo ""
    echo "Your existing public keys:"
    echo ""
    
    if [ -f ~/.ssh/id_rsa.pub ]; then
        echo "RSA Key:"
        cat ~/.ssh/id_rsa.pub
        echo ""
    fi
    
    if [ -f ~/.ssh/id_ed25519.pub ]; then
        echo "ED25519 Key (recommended):"
        cat ~/.ssh/id_ed25519.pub
        echo ""
    fi
    
    echo "📋 TO ADD TO DIGITAL OCEAN:"
    echo "1. Copy one of the keys above"
    echo "2. Click 'New SSH Key' button in Digital Ocean"
    echo "3. Paste the key and give it a name (e.g., 'My MacBook')"
    echo ""
else
    echo "No SSH keys found. Let's create one!"
    echo ""
    echo "📝 Enter your email address (for the key label):"
    read -p "Email: " email
    
    echo ""
    echo "Creating SSH key..."
    
    # Generate ED25519 key (more secure and modern than RSA)
    ssh-keygen -t ed25519 -C "$email" -f ~/.ssh/id_ed25519 -N ""
    
    # Start ssh-agent and add key
    eval "$(ssh-agent -s)"
    ssh-add ~/.ssh/id_ed25519
    
    # Add to SSH config for automatic loading
    if [ ! -f ~/.ssh/config ]; then
        touch ~/.ssh/config
    fi
    
    if ! grep -q "AddKeysToAgent" ~/.ssh/config; then
        echo "" >> ~/.ssh/config
        echo "Host *" >> ~/.ssh/config
        echo "  AddKeysToAgent yes" >> ~/.ssh/config
        echo "  UseKeychain yes" >> ~/.ssh/config
        echo "  IdentityFile ~/.ssh/id_ed25519" >> ~/.ssh/config
    fi
    
    echo ""
    echo "✅ SSH Key created successfully!"
    echo ""
    echo "📋 YOUR PUBLIC KEY (copy this entire line):"
    echo ""
    cat ~/.ssh/id_ed25519.pub
    echo ""
    echo "📋 TO ADD TO DIGITAL OCEAN:"
    echo "1. Copy the key above (the entire line starting with 'ssh-ed25519')"
    echo "2. Click 'New SSH Key' button in Digital Ocean"
    echo "3. Paste the key"
    echo "4. Name it something like 'My MacBook' or your computer name"
    echo "5. Click 'Add SSH Key'"
fi

echo ""
echo "🎯 NEXT STEPS:"
echo "1. Add the key to Digital Ocean (as described above)"
echo "2. Select the key checkbox in Digital Ocean"
echo "3. Continue creating your droplet"
echo ""
echo "Once your droplet is created, you'll connect with:"
echo "ssh root@YOUR_DROPLET_IP"
echo ""
echo "No password needed - your SSH key handles authentication!"