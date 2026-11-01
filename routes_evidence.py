from flask import Blueprint, request, jsonify
from models import db, Evidence
from datetime import datetime

evidence_bp = Blueprint('evidence', __name__, url_prefix='/api/v1')

# GET: Danh sách evidence
@evidence_bp.route('/tasks/<task_id>/evidences', methods=['GET'])
def get_evidences(task_id):
    """Lấy danh sách bằng chứng của một task"""
    try:
        evidences = Evidence.query.filter_by(task_id=task_id).all()
        
        return jsonify({
            'success': True,
            'data': [evidence.to_dict() for evidence in evidences]
        }), 200
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# POST: Thêm evidence
@evidence_bp.route('/tasks/<task_id>/evidences', methods=['POST'])
def create_evidence(task_id):
    """Thêm bằng chứng cho task"""
    try:
        data = request.get_json()
        
        evidence = Evidence(
            task_id=task_id,
            content=data.get('content'),
            evidence_type=data.get('evidence_type', 'log')
        )
        
        db.session.add(evidence)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'data': evidence.to_dict()
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

# DELETE: Xóa evidence
@evidence_bp.route('/evidences/<evidence_id>', methods=['DELETE'])
def delete_evidence(evidence_id):
    """Xóa bằng chứng"""
    try:
        evidence = Evidence.query.get(evidence_id)
        if not evidence:
            return jsonify({'success': False, 'error': 'Evidence not found'}), 404
        
        db.session.delete(evidence)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Evidence deleted successfully'
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500
