#!/bin/bash
# Quick fix for email module conflict

echo "🔧 Fixing email module naming conflict..."

cd /home/amd-knights/Paralegal/AMD_server/ml_pipeline

# Rename the email directory to avoid conflict with built-in email module
if [ -d "email" ]; then
    echo "Renaming 'email/' to 'email_processing/'"
    mv email email_processing
    
    # Update imports in the renamed files
    find email_processing -name "*.py" -type f -exec sed -i 's/from email\./from email_processing./g' {} \;
    find email_processing -name "*.py" -type f -exec sed -i 's/import email\./import email_processing./g' {} \;
    
    echo "✅ Fixed naming conflict"
else
    echo "✅ No conflict found"
fi

# Now run the embeddings script
echo ""
echo "Running FAISS embeddings generation..."
python rag_embeddings.py
