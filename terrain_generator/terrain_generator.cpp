#include <iostream>
#include <vector>
#include <unordered_map>
#include <random>
#include <cmath>
#include <functional>
#include <memory>
#include <cstring>

// SimplexNoise implementation
class SimplexNoise {
private:
    std::vector<int> perm;
    
    const double F2 = 0.5 * (sqrt(3.0) - 1.0);
    const double G2 = (3.0 - sqrt(3.0)) / 6.0;
    
    double dot(const int* g, double x, double y) {
        return g[0] * x + g[1] * y;
    }
    
    const int grad3[12][3] = {
        {1,1,0}, {-1,1,0}, {1,-1,0}, {-1,-1,0},
        {1,0,1}, {-1,0,1}, {1,0,-1}, {-1,0,-1},
        {0,1,1}, {0,-1,1}, {0,1,-1}, {0,-1,-1}
    };

public:
    SimplexNoise(int seed) {
        perm.resize(512);
        std::vector<int> p(256);
        
        // Initialize with values 0-255
        for (int i = 0; i < 256; i++) {
            p[i] = i;
        }
        
        // Shuffle based on seed
        std::mt19937 rng(seed);
        std::shuffle(p.begin(), p.end(), rng);
        
        // Duplicate to avoid buffer overflow
        for (int i = 0; i < 256; i++) {
            perm[i] = perm[i + 256] = p[i];
        }
    }
    
    double noise(double xin, double yin) {
        double n0, n1, n2; // Noise contributions from the three corners
        
        // Skew the input space to determine which simplex cell we're in
        double s = (xin + yin) * F2; // Hairy factor for 2D
        int i = floor(xin + s);
        int j = floor(yin + s);
        
        double t = (i + j) * G2;
        double X0 = i - t; // Unskew the cell origin back to (x,y) space
        double Y0 = j - t;
        double x0 = xin - X0; // The x,y distances from the cell origin
        double y0 = yin - Y0;
        
        // For the 2D case, the simplex shape is an equilateral triangle.
        // Determine which simplex we are in.
        int i1, j1; // Offsets for second (middle) corner of simplex in (i,j) coords
        if (x0 > y0) { // lower triangle, XY order: (0,0)->(1,0)->(1,1)
            i1 = 1;
            j1 = 0;
        } else { // upper triangle, YX order: (0,0)->(0,1)->(1,1)
            i1 = 0;
            j1 = 1;
        }
        
        // A step of (1,0) in (i,j) means a step of (1-c,-c) in (x,y), and
        // a step of (0,1) in (i,j) means a step of (-c,1-c) in (x,y), where
        // c = (3-sqrt(3))/6
        double x1 = x0 - i1 + G2; // Offsets for middle corner in (x,y) unskewed coords
        double y1 = y0 - j1 + G2;
        double x2 = x0 - 1.0 + 2.0 * G2; // Offsets for last corner in (x,y) unskewed coords
        double y2 = y0 - 1.0 + 2.0 * G2;
        
        // Work out the hashed gradient indices of the three simplex corners
        int ii = i & 255;
        int jj = j & 255;
        int gi0 = perm[ii + perm[jj]] % 12;
        int gi1 = perm[ii + i1 + perm[jj + j1]] % 12;
        int gi2 = perm[ii + 1 + perm[jj + 1]] % 12;
        
        // Calculate the contribution from the three corners
        double t0 = 0.5 - x0 * x0 - y0 * y0;
        if (t0 < 0) {
            n0 = 0.0;
        } else {
            t0 *= t0;
            n0 = t0 * t0 * dot(grad3[gi0], x0, y0);  // (x,y) of grad3 used for 2D gradient
        }
        
        double t1 = 0.5 - x1 * x1 - y1 * y1;
        if (t1 < 0) {
            n1 = 0.0;
        } else {
            t1 *= t1;
            n1 = t1 * t1 * dot(grad3[gi1], x1, y1);
        }
        
        double t2 = 0.5 - x2 * x2 - y2 * y2;
        if (t2 < 0) {
            n2 = 0.0;
        } else {
            t2 *= t2;
            n2 = t2 * t2 * dot(grad3[gi2], x2, y2);
        }
        
        // Add contributions from each corner to get the final noise value.
        // The result is scaled to return values in the interval [-1,1].
        return 70.0 * (n0 + n1 + n2);
    }
};

// Hash pair for chunk coordinates
struct ChunkCoordHash {
    std::size_t operator()(const std::pair<int, int>& p) const {
        return std::hash<int>()(p.first) ^ (std::hash<int>()(p.second) << 1);
    }
};

// Main TerrainGenerator class
class TerrainGenerator {
private:
    int width;
    int height;
    int maxElevation;
    int chunkSize;
    int seed;
    
    double scale;
    int octaves;
    double persistence;
    double lacunarity;
    double obstacleProb;
    
    SimplexNoise noiseGen;
    
    // Cache of generated chunks
    std::unordered_map<std::pair<int, int>, std::vector<float>, ChunkCoordHash> chunks;
    std::mt19937 rng;

public:
    TerrainGenerator(int width, int height, int maxElevation, int chunkSize, int seed) 
        : width(width), height(height), maxElevation(maxElevation), chunkSize(chunkSize), 
          seed(seed), noiseGen(seed), rng(seed) {
        
        // Default terrain parameters
        scale = 0.01;
        octaves = 6;
        persistence = 0.5;
        lacunarity = 2.0;
        obstacleProb = 0.2;
    }
    
    // Set terrain generation parameters
    void setParameters(double scale, int octaves, double persistence, double lacunarity, double obstacleProb) {
        this->scale = scale;
        this->octaves = octaves;
        this->persistence = persistence;
        this->lacunarity = lacunarity;
        this->obstacleProb = obstacleProb;
    }
    
    // Get chunk by coordinates
    std::vector<float> generateChunk(int chunkX, int chunkY) {
        // Check if chunk already exists in cache
        std::pair<int, int> chunkKey(chunkX, chunkY);
        if (chunks.find(chunkKey) != chunks.end()) {
            return chunks[chunkKey];
        }
        
        // Create a new chunk
        std::vector<float> chunk(chunkSize * chunkSize, 0.0f);
        
        // Calculate absolute position of chunk
        int absX = chunkX * chunkSize;
        int absY = chunkY * chunkSize;
        
        // Generate elevation values using simplex noise
        std::uniform_real_distribution<double> dist(0.0, 1.0);
        
        for (int x = 0; x < chunkSize; x++) {
            for (int y = 0; y < chunkSize; y++) {
                // Calculate absolute coordinates
                int worldX = absX + x;
                int worldY = absY + y;
                
                // Generate elevation using multiple octaves of noise
                double elevation = 0.0;
                double amplitude = 1.0;
                double frequency = 1.0;
                
                for (int i = 0; i < octaves; i++) {
                    double nx = worldX * scale * frequency;
                    double ny = worldY * scale * frequency;
                    
                    // Add noise contribution for this octave
                    elevation += noiseGen.noise(nx, ny) * amplitude;
                    
                    // Update amplitude and frequency for next octave
                    amplitude *= persistence;
                    frequency *= lacunarity;
                }
                
                // Normalize elevation to [0, 1] range
                elevation = (elevation + 1.0) / 2.0;
                
                // Scale to max elevation
                elevation *= maxElevation;
                
                // Randomly place obstacles (represented by -1)
                if (dist(rng) < obstacleProb) {
                    chunk[x * chunkSize + y] = -1.0f;
                } else {
                    chunk[x * chunkSize + y] = static_cast<float>(elevation);
                }
            }
        }
        
        // Store the generated chunk in cache
        chunks[chunkKey] = chunk;
        
        return chunk;
    }
    
    // Get elevation at specified world coordinates
    float getElevation(int x, int y) {
        // Check if coordinates are within bounds
        if (x < 0 || x >= width || y < 0 || y >= height) {
            return -1.0f;  // Out of bounds - treated as obstacle
        }
        
        // Calculate chunk coordinates
        int chunkX = x / chunkSize;
        int chunkY = y / chunkSize;
        
        // Calculate local coordinates within chunk
        int localX = x % chunkSize;
        int localY = y % chunkSize;
        
        // Get or generate the chunk
        std::vector<float> chunk = generateChunk(chunkX, chunkY);
        
        // Return elevation at specified position
        return chunk[localX * chunkSize + localY];
    }
    
    // Check if a position is an obstacle
    bool isObstacle(int x, int y) {
        return getElevation(x, y) < 0;
    }
    
    // Unload distant chunks to save memory
    void unloadDistantChunks(int centerX, int centerY, int maxViewRadius) {
        int centerChunkX = centerX / chunkSize;
        int centerChunkY = centerY / chunkSize;
        
        // Find chunks to remove
        std::vector<std::pair<int, int>> chunksToRemove;
        
        for (const auto& entry : chunks) {
            int chunkX = entry.first.first;
            int chunkY = entry.first.second;
            
            // Calculate Manhattan distance to center chunk
            int dx = std::abs(chunkX - centerChunkX);
            int dy = std::abs(chunkY - centerChunkY);
            int distance = dx + dy;
            
            // If chunk is too far, mark for removal
            if (distance > maxViewRadius) {
                chunksToRemove.push_back(entry.first);
            }
        }
        
        // Remove distant chunks
        for (const auto& key : chunksToRemove) {
            chunks.erase(key);
        }
    }
    
    // Get visible chunks from center point
    std::vector<std::pair<int, int>> getVisibleChunks(int centerX, int centerY, int viewRadius) {
        int centerChunkX = centerX / chunkSize;
        int centerChunkY = centerY / chunkSize;
        
        std::vector<std::pair<int, int>> visibleChunks;
        
        for (int dx = -viewRadius; dx <= viewRadius; dx++) {
            for (int dy = -viewRadius; dy <= viewRadius; dy++) {
                int chunkX = centerChunkX + dx;
                int chunkY = centerChunkY + dy;
                
                // Ensure chunk is within world bounds
                if (chunkX >= 0 && chunkX < width / chunkSize &&
                    chunkY >= 0 && chunkY < height / chunkSize) {
                    visibleChunks.push_back({chunkX, chunkY});
                }
            }
        }
        
        return visibleChunks;
    }
    
    // Clear all generated chunks from memory
    void clearChunks() {
        chunks.clear();
    }
};

extern "C" {
    // Create and manage terrain generator instances
    TerrainGenerator* terrain_create(int width, int height, int maxElevation, int chunkSize, int seed) {
        return new TerrainGenerator(width, height, maxElevation, chunkSize, seed);
    }
    
    void terrain_set_parameters(TerrainGenerator* terrain, double scale, int octaves, 
                             double persistence, double lacunarity, double obstacleProb) {
        if (terrain) {
            terrain->setParameters(scale, octaves, persistence, lacunarity, obstacleProb);
        }
    }
    
    // Get and copy chunk data
    void terrain_generate_chunk(TerrainGenerator* terrain, int chunkX, int chunkY, float* result) {
        if (!terrain || !result) return;
        
        std::vector<float> chunk = terrain->generateChunk(chunkX, chunkY);
        std::memcpy(result, chunk.data(), chunk.size() * sizeof(float));
    }
    
    float terrain_get_elevation(TerrainGenerator* terrain, int x, int y) {
        if (!terrain) return -1.0f;
        return terrain->getElevation(x, y);
    }
    
    bool terrain_is_obstacle(TerrainGenerator* terrain, int x, int y) {
        if (!terrain) return true;
        return terrain->isObstacle(x, y);
    }
    
    void terrain_unload_distant_chunks(TerrainGenerator* terrain, int centerX, int centerY, int maxViewRadius) {
        if (terrain) {
            terrain->unloadDistantChunks(centerX, centerY, maxViewRadius);
        }
    }
    
    void terrain_clear_chunks(TerrainGenerator* terrain) {
        if (terrain) {
            terrain->clearChunks();
        }
    }
    
    void terrain_destroy(TerrainGenerator* terrain) {
        delete terrain;
    }
} 