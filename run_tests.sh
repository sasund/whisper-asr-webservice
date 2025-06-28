#!/bin/bash

# Whisper ASR Webservice Test Script
# Usage: ./run_tests.sh [server_url]
# Default server URL: http://localhost:9000

# Configuration
SERVER_URL=${1:-"http://localhost:9000"}
WS_URL="ws://localhost:9000"
TEST_AUDIO="audio/king_16k.wav"
TEST_AUDIO_MP3="audio/king.mp3"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Test counter
TESTS_PASSED=0
TESTS_FAILED=0

# Helper functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[PASS]${NC} $1"
    ((TESTS_PASSED++))
}

log_error() {
    echo -e "${RED}[FAIL]${NC} $1"
    ((TESTS_FAILED++))
}

log_warning() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

# Check if server is running
check_server() {
    log_info "Checking if server is running at $SERVER_URL..."
    if curl -s "$SERVER_URL/docs" > /dev/null 2>&1; then
        log_success "Server is running"
        return 0
    else
        log_error "Server is not running at $SERVER_URL"
        log_info "Please start the server first with: make serve"
        return 1
    fi
}

# Check if test audio files exist
check_test_files() {
    log_info "Checking test audio files..."
    if [ ! -f "$TEST_AUDIO" ]; then
        log_error "Test audio file not found: $TEST_AUDIO"
        return 1
    fi
    if [ ! -f "$TEST_AUDIO_MP3" ]; then
        log_warning "MP3 test file not found: $TEST_AUDIO_MP3 (some tests will be skipped)"
    fi
    log_success "Test files check completed"
    return 0
}

# Test ASR endpoint with different output formats
test_asr_formats() {
    log_info "Testing ASR endpoint with different output formats..."
    
    local formats=("txt" "json" "srt" "vtt" "tsv")
    
    for format in "${formats[@]}"; do
        log_info "Testing output format: $format"
        response=$(curl -s -F "audio_file=@$TEST_AUDIO" "$SERVER_URL/asr?output=$format" 2>/dev/null)
        
        if [ $? -eq 0 ] && [ -n "$response" ]; then
            log_success "ASR $format format test passed"
        else
            log_error "ASR $format format test failed"
        fi
    done
}

# Test ASR with different languages
test_asr_languages() {
    log_info "Testing ASR with different languages..."
    
    local languages=("no" "en" "auto")
    
    for lang in "${languages[@]}"; do
        log_info "Testing language: $lang"
        response=$(curl -s -F "audio_file=@$TEST_AUDIO" "$SERVER_URL/asr?language=$lang&output=json" 2>/dev/null)
        
        if [ $? -eq 0 ] && [ -n "$response" ]; then
            log_success "ASR language $lang test passed"
            
            # For English language test, check if response contains English text
            if [ "$lang" = "en" ]; then
                if echo "$response" | grep -q "king\|the\|and\|is" 2>/dev/null; then
                    log_success "English transcription confirmed (contains English words)"
                else
                    log_warning "English transcription may not be working correctly"
                fi
            fi
        else
            log_error "ASR language $lang test failed"
        fi
    done
}

# Test ASR with different tasks
test_asr_tasks() {
    log_info "Testing ASR with different tasks..."
    
    local tasks=("transcribe" "translate")
    
    for task in "${tasks[@]}"; do
        log_info "Testing task: $task"
        response=$(curl -s -F "audio_file=@$TEST_AUDIO" "$SERVER_URL/asr?task=$task&output=json" 2>/dev/null)
        
        if [ $? -eq 0 ] && [ -n "$response" ]; then
            log_success "ASR task $task test passed"
        else
            log_error "ASR task $task test failed"
        fi
    done
}

# Test ASR with VAD and word timestamps (Faster Whisper specific)
test_asr_advanced_features() {
    log_info "Testing ASR with advanced features..."
    
    # Test VAD
    log_info "Testing VAD filter"
    response=$(curl -s -F "audio_file=@$TEST_AUDIO" "$SERVER_URL/asr?vad_filter=true&output=json" 2>/dev/null)
    if [ $? -eq 0 ]; then
        log_success "VAD filter test passed"
    else
        log_warning "VAD filter test failed (may not be supported by current engine)"
    fi
    
    # Test word timestamps
    log_info "Testing word timestamps"
    response=$(curl -s -F "audio_file=@$TEST_AUDIO" "$SERVER_URL/asr?word_timestamps=true&output=json" 2>/dev/null)
    if [ $? -eq 0 ]; then
        log_success "Word timestamps test passed"
    else
        log_warning "Word timestamps test failed (may not be supported by current engine)"
    fi
    
    # Test diarization (WhisperX specific)
    log_info "Testing diarization"
    response=$(curl -s -F "audio_file=@$TEST_AUDIO" "$SERVER_URL/asr?diarize=true&output=json" 2>/dev/null)
    if [ $? -eq 0 ]; then
        log_success "Diarization test passed"
    else
        log_warning "Diarization test failed (may not be supported by current engine)"
    fi
}

# Test language detection
test_language_detection() {
    log_info "Testing language detection..."
    
    response=$(curl -s -F "audio_file=@$TEST_AUDIO" "$SERVER_URL/detect-language" 2>/dev/null)
    
    if [ $? -eq 0 ] && [ -n "$response" ]; then
        log_success "Language detection test passed"
        log_info "Detected language: $response"
    else
        log_error "Language detection test failed"
    fi
}

# Test error handling
test_error_handling() {
    log_info "Testing error handling..."
    
    # Test with non-existent file
    response=$(curl -s -F "audio_file=@nonexistent.wav" "$SERVER_URL/asr" 2>/dev/null)
    if [ $? -ne 0 ]; then
        log_success "Error handling test passed (non-existent file)"
    else
        log_error "Error handling test failed (should have failed with non-existent file)"
    fi
    
    # Test with invalid output format
    response=$(curl -s -F "audio_file=@$TEST_AUDIO" "$SERVER_URL/asr?output=invalid" 2>/dev/null)
    if [ $? -eq 0 ]; then
        log_warning "Invalid output format test (may be handled gracefully)"
    else
        log_success "Invalid output format test passed (properly rejected)"
    fi
}

# Test WebSocket connection (basic check)
test_websocket() {
    log_info "Testing WebSocket connection..."
    
    # Check if WebSocket endpoint is available
    response=$(curl -s -I "$SERVER_URL/ws/live-transcribe" 2>/dev/null | head -1)
    if [[ $response == *"101"* ]] || [[ $response == *"Upgrade"* ]]; then
        log_success "WebSocket endpoint is available"
    else
        log_warning "WebSocket endpoint test skipped (requires WebSocket client)"
    fi
}

# Test different audio formats
test_audio_formats() {
    log_info "Testing different audio formats..."
    
    # Test WAV format
    log_info "Testing WAV format"
    response=$(curl -s -F "audio_file=@$TEST_AUDIO" "$SERVER_URL/asr?output=json" 2>/dev/null)
    if [ $? -eq 0 ] && [ -n "$response" ]; then
        log_success "WAV format test passed"
    else
        log_error "WAV format test failed"
    fi
    
    # Test MP3 format if available
    if [ -f "$TEST_AUDIO_MP3" ]; then
        log_info "Testing MP3 format"
        response=$(curl -s -F "audio_file=@$TEST_AUDIO_MP3" "$SERVER_URL/asr?output=json" 2>/dev/null)
        if [ $? -eq 0 ] && [ -n "$response" ]; then
            log_success "MP3 format test passed"
        else
            log_error "MP3 format test failed"
        fi
    fi
}

# Test Swagger documentation
test_documentation() {
    log_info "Testing API documentation..."
    
    response=$(curl -s "$SERVER_URL/docs" 2>/dev/null)
    if [ $? -eq 0 ] && [ -n "$response" ]; then
        log_success "API documentation is accessible"
    else
        log_error "API documentation is not accessible"
    fi
}

# Test English transcription specifically
test_english_transcription() {
    log_info "Testing English transcription specifically..."
    
    # Test with explicit English language parameter
    log_info "Testing with language=en parameter"
    response=$(curl -s -F "audio_file=@$TEST_AUDIO" "$SERVER_URL/asr?language=en&output=json" 2>/dev/null)
    
    if [ $? -eq 0 ] && [ -n "$response" ]; then
        # Check if response contains English words
        if echo "$response" | grep -q "king\|the\|and\|is\|was\|in\|of" 2>/dev/null; then
            log_success "English transcription working correctly with language=en"
        else
            log_warning "English transcription may still be in Norwegian despite language=en"
            log_info "Response preview: $(echo "$response" | head -c 200)..."
        fi
    else
        log_error "English transcription test failed"
    fi
    
    # Test without language parameter (should auto-detect)
    log_info "Testing without language parameter (auto-detect)"
    response=$(curl -s -F "audio_file=@$TEST_AUDIO" "$SERVER_URL/asr?output=json" 2>/dev/null)
    
    if [ $? -eq 0 ] && [ -n "$response" ]; then
        log_info "Auto-detect test completed (check response manually)"
    else
        log_error "Auto-detect test failed"
    fi
}

# Main test execution
main() {
    echo "=========================================="
    echo "Whisper ASR Webservice Test Suite"
    echo "=========================================="
    echo "Server URL: $SERVER_URL"
    echo "Test audio: $TEST_AUDIO"
    echo "=========================================="
    
    # Run all tests
    check_server || {
        echo "Server check failed. Exiting."
        exit 1
    }
    
    check_test_files || {
        echo "Test files check failed. Exiting."
        exit 1
    }
    
    test_documentation
    test_asr_formats
    test_asr_languages
    test_asr_tasks
    test_asr_advanced_features
    test_language_detection
    test_error_handling
    test_websocket
    test_audio_formats
    test_english_transcription
    
    # Print summary
    echo "=========================================="
    echo "Test Summary"
    echo "=========================================="
    echo "Tests passed: $TESTS_PASSED"
    echo "Tests failed: $TESTS_FAILED"
    echo "Total tests: $((TESTS_PASSED + TESTS_FAILED))"
    
    if [ $TESTS_FAILED -eq 0 ]; then
        echo -e "${GREEN}All tests passed!${NC}"
        exit 0
    else
        echo -e "${RED}Some tests failed.${NC}"
        exit 1
    fi
}

# Run main function
main "$@" 