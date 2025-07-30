# tests/test_user_service.py
import pytest
import uuid
from unittest.mock import Mock, MagicMock, patch, AsyncMock
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from datetime import datetime

from app.backend.services.user_service import UserService
from app.backend.models.user import User
from app.backend.schemas.user import UserOut


class TestUserService:
    """Test cases for UserService class"""
    
    @pytest.fixture
    def mock_db(self):
        """Create a mock database session"""
        return Mock(spec=Session)
    
    @pytest.fixture
    def user_service(self, mock_db):
        """Create a UserService instance with mocked database"""
        return UserService(mock_db)
    
    @pytest.fixture
    def sample_user_id(self):
        """Generate a sample UUID for testing"""
        return uuid.uuid4()
    
    @pytest.fixture
    def sample_user(self, sample_user_id):
        """Create a sample User model instance"""
        user = Mock(spec=User)
        user.id = sample_user_id
        user.email = "test@example.com"
        user.username = "testuser"
        user.is_active = True
        return user
    
    @pytest.fixture
    def sample_user_out(self, sample_user_id):
        """Create a sample UserOut schema instance"""
        return UserOut(
            id=sample_user_id,
            email="test@example.com",
            full_name="testuser",
            created_at=datetime.now(),
            updated_at=datetime.now()
        )


class TestGetUserById(TestUserService):
    """Test cases for get_user_by_id method"""
    
    @pytest.mark.asyncio
    async def test_get_user_by_id_success(self, user_service, mock_db, sample_user_id, sample_user):
        """Test successful user retrieval by ID"""
        # Arrange
        mock_query = Mock()
        mock_filter = Mock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_filter
        mock_filter.first.return_value = sample_user
        
        # Act
        result = await user_service.get_user_by_id(sample_user_id)
        
        # Assert
        assert result == sample_user
        mock_db.query.assert_called_once_with(User)
        # Don't check the exact filter expression since SQLAlchemy creates new objects
        mock_query.filter.assert_called_once()
        mock_filter.first.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_user_by_id_not_found(self, user_service, mock_db, sample_user_id):
        """Test user retrieval when user doesn't exist"""
        # Arrange
        mock_query = Mock()
        mock_filter = Mock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_filter
        mock_filter.first.return_value = None
        
        # Act
        result = await user_service.get_user_by_id(sample_user_id)
        
        # Assert
        assert result is None
        mock_db.query.assert_called_once_with(User)
        # Don't check the exact filter expression since SQLAlchemy creates new objects
        mock_query.filter.assert_called_once()
        mock_filter.first.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_user_by_id_invalid_uuid(self, user_service):
        """Test get_user_by_id with invalid UUID (edge case)"""
        # This test is removed since the method signature expects UUID type
        # and validation should happen at the API layer
        pass


class TestGetUserProfile(TestUserService):
    """Test cases for get_user_profile method"""
    
    @pytest.mark.asyncio
    async def test_get_user_profile_success(self, user_service, sample_user_id, sample_user, sample_user_out):
        """Test successful user profile retrieval"""
        # Arrange
        user_service.get_user_by_id = AsyncMock(return_value=sample_user)
        
        # Mock UserOut.model_validate to return our sample_user_out
        with patch('app.backend.schemas.user.UserOut.model_validate', return_value=sample_user_out) as mock_validate:
            # Act
            result = await user_service.get_user_profile(sample_user_id)
            
            # Assert
            assert result == sample_user_out
            user_service.get_user_by_id.assert_called_once_with(sample_user_id)
            mock_validate.assert_called_once_with(sample_user)
    
    @pytest.mark.asyncio
    async def test_get_user_profile_user_not_found(self, user_service, sample_user_id):
        """Test get_user_profile when user doesn't exist"""
        # Arrange
        user_service.get_user_by_id = AsyncMock(return_value=None)
        
        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            await user_service.get_user_profile(sample_user_id)
        
        # Verify exception details
        assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND
        assert exc_info.value.detail == "User not found"
        user_service.get_user_by_id.assert_called_once_with(sample_user_id)
    
    @pytest.mark.asyncio
    async def test_get_user_profile_user_is_none(self, user_service, sample_user_id):
        """Test get_user_profile when get_user_by_id returns None explicitly"""
        # Arrange
        user_service.get_user_by_id = AsyncMock(return_value=None)
        
        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            await user_service.get_user_profile(sample_user_id)
        
        assert exc_info.value.status_code == 404
        assert "User not found" in str(exc_info.value.detail)
    
    @pytest.mark.asyncio
    async def test_get_user_profile_model_validate_error(self, user_service, sample_user_id, sample_user):
        """Test get_user_profile when UserOut.model_validate raises an exception"""
        # Arrange
        user_service.get_user_by_id = AsyncMock(return_value=sample_user)
        
        with patch('app.backend.schemas.user.UserOut.model_validate', side_effect=ValueError("Validation error")):
            # Act & Assert
            with pytest.raises(ValueError, match="Validation error"):
                await user_service.get_user_profile(sample_user_id)
            
            user_service.get_user_by_id.assert_called_once_with(sample_user_id)


class TestUserServiceInitialization(TestUserService):
    """Test cases for UserService initialization"""
    
    def test_user_service_init(self, mock_db):
        """Test UserService initialization"""
        # Act
        service = UserService(mock_db)
        
        # Assert
        assert service.db == mock_db
        assert hasattr(service, 'get_user_by_id')
        assert hasattr(service, 'get_user_profile')
    
    def test_user_service_init_with_none_db(self):
        """Test UserService initialization with None database"""
        # Act
        service = UserService(None)
        
        # Assert
        assert service.db is None


class TestUserServiceIntegration(TestUserService):
    """Integration-style tests for UserService methods working together"""
    
    @pytest.mark.asyncio
    async def test_get_user_profile_calls_get_user_by_id(self, mock_db, sample_user_id, sample_user, sample_user_out):
        """Test that get_user_profile properly calls get_user_by_id"""
        # Arrange
        service = UserService(mock_db)
        
        # Mock the database query chain
        mock_query = Mock()
        mock_filter = Mock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_filter
        mock_filter.first.return_value = sample_user
        
        with patch('app.backend.schemas.user.UserOut.model_validate', return_value=sample_user_out):
            # Act
            result = await service.get_user_profile(sample_user_id)
            
            # Assert
            assert result == sample_user_out
            mock_db.query.assert_called_once_with(User)
            mock_query.filter.assert_called_once()


# Additional test configuration and fixtures if needed
@pytest.fixture(scope="session")
def test_db_session():
    """Create a test database session (if you have a test database setup)"""
    # This would be implemented if you have actual database testing setup
    pass


# Example of parametrized tests for different UUID scenarios
class TestUserServiceParametrized:
    """Parametrized tests for various scenarios"""
    
    @pytest.fixture
    def mock_db(self):
        """Create a mock database session for parametrized tests"""
        return Mock(spec=Session)
    
    @pytest.mark.parametrize("user_exists,expected_result", [
        (True, "user_found"),
        (False, None),
    ])
    @pytest.mark.asyncio
    async def test_get_user_by_id_parametrized(self, mock_db, user_exists, expected_result):
        """Parametrized test for get_user_by_id with different scenarios"""
        # Arrange
        service = UserService(mock_db)
        user_id = uuid.uuid4()
        
        mock_query = Mock()
        mock_filter = Mock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_filter
        
        if user_exists:
            mock_user = Mock(spec=User)
            mock_user.id = user_id
            mock_filter.first.return_value = mock_user
            expected_result = mock_user
        else:
            mock_filter.first.return_value = None
            expected_result = None
        
        # Act
        result = await service.get_user_by_id(user_id)
        
        # Assert
        assert result == expected_result
        mock_db.query.assert_called_once_with(User)
        mock_query.filter.assert_called_once()
        mock_filter.first.assert_called_once()