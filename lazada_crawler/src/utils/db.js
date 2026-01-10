const { createClient } = require('@supabase/supabase-js');
require('dotenv').config();

// Kiểm tra env variables
if (!process.env.SUPABASE_URL || !process.env.SUPABASE_KEY) {
  console.error('❌ Thiếu SUPABASE_URL hoặc SUPABASE_KEY trong file .env');
  process.exit(1);
}

const supabase = createClient(
  process.env.SUPABASE_URL,
  process.env.SUPABASE_KEY
);

async function productExists(platform, siteProductId) {
  try {
    const { data, error } = await supabase
      .from('products')
      .select('id')
      .eq('platform', platform)
      .eq('site_product_id', siteProductId)
      .maybeSingle();
    
    if (error && error.code !== 'PGRST116') {
      console.error('Lỗi kiểm tra sản phẩm:', error.message);
      return false;
    }
    
    return data !== null;
  } catch (error) {
    console.error('Lỗi kiểm tra sản phẩm:', error.message);
    return false;
  }
}

async function upsertProduct(data) {
  try {
    const productData = {
      platform: data.platform,
      site_product_id: data.site_product_id,
      product_name: data.product_name,
      price: data.price,
      original_price: data.original_price,
      discount_percent: data.discount_percent,
      product_url: data.product_url,
      image_url: data.image_url,
      rating: data.rating,
      review_count: data.review_count,
      location: data.location,
      category: data.category,
      last_seen_at: new Date().toISOString()
    };

    const { data: result, error } = await supabase
      .from('products')
      .upsert(productData, {
        onConflict: 'platform,site_product_id'
      })
      .select('id')
      .single();
    
    if (error) {
      console.error('Lỗi lưu sản phẩm:', error.message);
      return null;
    }
    
    return result ? result.id : null;
  } catch (error) {
    console.error('Lỗi lưu sản phẩm:', error.message);
    return null;
  }
}

async function testConnection() {
  try {
    const { count, error } = await supabase
      .from('products')
      .select('*', { count: 'exact', head: true });
    
    if (error) {
      console.error('❌ Lỗi kết nối Supabase:', error.message);
      console.error('Chi tiết:', error);
      return false;
    }
    
    console.log('✅ Kết nối Supabase thành công!');
    console.log(`📊 Hiện có ${count || 0} sản phẩm trong database`);
    return true;
  } catch (error) {
    console.error('❌ Lỗi kết nối:', error.message);
    return false;
  }
}

module.exports = { productExists, upsertProduct, testConnection };