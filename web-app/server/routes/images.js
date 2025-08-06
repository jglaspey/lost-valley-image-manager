const express = require('express');
const router = express.Router();
const db = require('../database/connection');

// Initialize database connection
db.connect().catch(console.error);

// GET /api/images - Get paginated images with optional filters
router.get('/', async (req, res) => {
  try {
    const {
      page = 1,
      limit = 20,
      sort = 'created_date',
      order = 'DESC',
      status = 'completed'
    } = req.query;

    const offset = (parseInt(page) - 1) * parseInt(limit);

    // Base query for completed images with metadata
    let query = `
      SELECT 
        f.id,
        f.filename,
        f.file_path,
        f.file_size,
        f.width,
        f.height,
        f.mime_type,
        f.created_date,
        f.modified_date,
        f.thumbnail_path,
        f.drive_file_id,
        f.processing_status,
        f.processed_at,
        m.primary_subject,
        m.visual_quality,
        m.has_people,
        m.people_count,
        m.is_indoor,
        m.social_media_score,
        m.social_media_reason,
        m.marketing_score,
        m.marketing_use,
        m.season,
        m.time_of_day,
        m.mood_energy,
        m.color_palette,
        m.notes,
        m.extracted_at
      FROM files f
      LEFT JOIN metadata m ON f.id = m.file_id
      WHERE f.mime_type LIKE 'image%'
    `;

    const params = [];

    // Add status filter
    if (status && status !== 'all') {
      query += ` AND f.processing_status = ?`;
      params.push(status);
    }

    // Add sorting
    const validSortColumns = ['created_date', 'filename', 'visual_quality', 'social_media_score', 'marketing_score'];
    const validOrders = ['ASC', 'DESC'];
    
    if (validSortColumns.includes(sort) && validOrders.includes(order.toUpperCase())) {
      const sortColumn = sort === 'created_date' ? 'f.created_date' : 
                        sort === 'filename' ? 'f.filename' :
                        `m.${sort}`;
      query += ` ORDER BY ${sortColumn} ${order.toUpperCase()}`;
    }

    // Add pagination
    query += ` LIMIT ? OFFSET ?`;
    params.push(parseInt(limit), offset);

    const images = await db.query(query, params);

    // Get activity tags for each image
    const imageIds = images.map(img => img.id);
    let activityTags = [];
    
    if (imageIds.length > 0) {
      const placeholders = imageIds.map(() => '?').join(',');
      const tagsQuery = `
        SELECT file_id, tag_name 
        FROM activity_tags 
        WHERE file_id IN (${placeholders})
      `;
      activityTags = await db.query(tagsQuery, imageIds);
    }

    // Group tags by file_id
    const tagsByFileId = activityTags.reduce((acc, tag) => {
      if (!acc[tag.file_id]) acc[tag.file_id] = [];
      acc[tag.file_id].push(tag.tag_name);
      return acc;
    }, {});

    // Add activity tags to images and generate URLs
    const imagesWithTags = images.map(image => ({
      ...image,
      activity_tags: tagsByFileId[image.id] || [],
      drive_view_url: `https://drive.google.com/file/d/${image.drive_file_id}/view`,
      drive_download_url: `https://drive.google.com/uc?id=${image.drive_file_id}`
    }));

    // Get total count for pagination
    let countQuery = `
      SELECT COUNT(*) as total
      FROM files f
      WHERE f.mime_type LIKE 'image%'
    `;
    const countParams = [];

    if (status && status !== 'all') {
      countQuery += ` AND f.processing_status = ?`;
      countParams.push(status);
    }

    const totalResult = await db.get(countQuery, countParams);
    const total = totalResult.total;

    res.json({
      images: imagesWithTags,
      pagination: {
        page: parseInt(page),
        limit: parseInt(limit),
        total,
        pages: Math.ceil(total / parseInt(limit))
      }
    });

  } catch (error) {
    console.error('Error fetching images:', error);
    res.status(500).json({ error: 'Internal server error' });
  }
});

// GET /api/images/:id - Get single image with full details
router.get('/:id', async (req, res) => {
  try {
    const { id } = req.params;

    const query = `
      SELECT 
        f.id,
        f.filename,
        f.file_path,
        f.file_size,
        f.width,
        f.height,
        f.mime_type,
        f.created_date,
        f.modified_date,
        f.thumbnail_path,
        f.drive_file_id,
        f.processing_status,
        f.processed_at,
        f.error_message,
        m.primary_subject,
        m.visual_quality,
        m.has_people,
        m.people_count,
        m.is_indoor,
        m.social_media_score,
        m.social_media_reason,
        m.marketing_score,
        m.marketing_use,
        m.season,
        m.time_of_day,
        m.mood_energy,
        m.color_palette,
        m.notes,
        m.extracted_at
      FROM files f
      LEFT JOIN metadata m ON f.id = m.file_id
      WHERE f.id = ?
    `;

    const image = await db.get(query, [id]);

    if (!image) {
      return res.status(404).json({ error: 'Image not found' });
    }

    // Get activity tags
    const tagsQuery = `
      SELECT tag_name 
      FROM activity_tags 
      WHERE file_id = ?
    `;
    const tags = await db.query(tagsQuery, [id]);
    
    const imageWithDetails = {
      ...image,
      activity_tags: tags.map(tag => tag.tag_name),
      drive_view_url: `https://drive.google.com/file/d/${image.drive_file_id}/view`,
      drive_download_url: `https://drive.google.com/uc?id=${image.drive_file_id}`
    };

    res.json(imageWithDetails);

  } catch (error) {
    console.error('Error fetching image:', error);
    res.status(500).json({ error: 'Internal server error' });
  }
});

// PUT /api/images/:id/metadata - Update image metadata
router.put('/:id/metadata', async (req, res) => {
  try {
    const { id } = req.params;
    const {
      primary_subject,
      visual_quality,
      has_people,
      people_count,
      is_indoor,
      social_media_score,
      social_media_reason,
      marketing_score,
      marketing_use,
      season,
      time_of_day,
      mood_energy,
      color_palette,
      notes,
      activity_tags
    } = req.body;

    // Validate required fields
    if (!primary_subject || !visual_quality || !social_media_score || !marketing_score) {
      return res.status(400).json({ error: 'Missing required metadata fields' });
    }

    // Validate ranges
    if (visual_quality < 1 || visual_quality > 5 || 
        social_media_score < 1 || social_media_score > 5 ||
        marketing_score < 1 || marketing_score > 5) {
      return res.status(400).json({ error: 'Scores must be between 1 and 5' });
    }

    // Check if image exists
    const existingImage = await db.get('SELECT id FROM files WHERE id = ?', [id]);
    if (!existingImage) {
      return res.status(404).json({ error: 'Image not found' });
    }

    // Update metadata
    const updateQuery = `
      UPDATE metadata SET
        primary_subject = ?,
        visual_quality = ?,
        has_people = ?,
        people_count = ?,
        is_indoor = ?,
        social_media_score = ?,
        social_media_reason = ?,
        marketing_score = ?,
        marketing_use = ?,
        season = ?,
        time_of_day = ?,
        mood_energy = ?,
        color_palette = ?,
        notes = ?
      WHERE file_id = ?
    `;

    await db.run(updateQuery, [
      primary_subject,
      visual_quality,
      has_people,
      people_count,
      is_indoor,
      social_media_score,
      social_media_reason,
      marketing_score,
      marketing_use,
      season,
      time_of_day,
      mood_energy,
      color_palette,
      notes,
      id
    ]);

    // Update activity tags
    if (activity_tags && Array.isArray(activity_tags)) {
      // Remove existing tags
      await db.run('DELETE FROM activity_tags WHERE file_id = ?', [id]);
      
      // Add new tags
      if (activity_tags.length > 0) {
        const insertTagsQuery = 'INSERT INTO activity_tags (file_id, tag_name) VALUES (?, ?)';
        for (const tag of activity_tags) {
          await db.run(insertTagsQuery, [id, tag]);
        }
      }
    }

    res.json({ message: 'Metadata updated successfully' });

  } catch (error) {
    console.error('Error updating metadata:', error);
    res.status(500).json({ error: 'Internal server error' });
  }
});

module.exports = router;